"""Upstream response envelopes and challenge detection (SPEC §2.3).

Upstream serves JSON under a ``text/html`` Content-Type, so parsing looks only at
the body content and never at headers. ``code == 999`` is the one business failure
that raises (``SessionExpired``); everything else is returned as data.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from .errors import ParseError, SessionExpired

_CHALLENGE_MARKERS = ("ydclearance", "fengkongcloud", "captcha")
_HTML_MARKERS = ("<html", "<!doctype", "<script")


@dataclass(frozen=True)
class Envelope:
    """A generic ``{"code": ..., "msg": ..., "data": ...}`` API envelope."""

    code: object
    msg: str
    data: object
    raw: object


@dataclass(frozen=True)
class UsersureResult:
    """The usersure endpoint response (a flat, non-envelope JSON object)."""

    ok: bool
    re_url: str | None
    code: str


def _loads(body: str | bytes, field_name: str) -> Any:
    """Decode *body* (bytes -> utf-8) and ``json.loads`` it, mapping failure to ParseError."""
    if isinstance(body, (bytes, bytearray)):
        try:
            body = bytes(body).decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ParseError(field_name, "<undecodable bytes>") from exc
    if not isinstance(body, str):
        raise ParseError(field_name, body)
    try:
        return json.loads(body)
    except ValueError as exc:
        raise ParseError(field_name, body) from exc


def parse_api_envelope(body: str | bytes) -> Envelope:
    """Parse an ``api.uyiban.com`` JSON envelope.

    Raises:
        ParseError: if *body* is not a JSON object.
        SessionExpired: if the envelope ``code`` is ``999``.
    """
    raw = _loads(body, "envelope")
    if not isinstance(raw, dict):
        raise ParseError("envelope", body)

    code = raw.get("code")
    if code == 999 or code == "999":
        msg = raw.get("msg")
        raise SessionExpired(msg if isinstance(msg, str) else "")

    msg = raw.get("msg")
    if not isinstance(msg, str):
        msg = "" if msg is None else str(msg)

    return Envelope(code=code, msg=msg, data=raw.get("data"), raw=raw)


def parse_usersure_response(body: str | bytes) -> UsersureResult:
    """Parse a usersure response.

    Business failure codes (e.g. ``e001``) are returned as data — only structural
    failures raise.

    Raises:
        ParseError: if *body* is not a JSON object.
    """
    raw = _loads(body, "usersure")
    if not isinstance(raw, dict):
        raise ParseError("usersure", body)

    raw_code = raw.get("code")
    code = raw_code if isinstance(raw_code, str) else ("" if raw_code is None else str(raw_code))

    re_url = raw.get("reUrl")
    if not isinstance(re_url, str) or not re_url:
        re_url = None

    return UsersureResult(ok=code == "s200", re_url=re_url, code=code)


def looks_like_challenge(body: str | bytes) -> bool:
    """Best-effort detection of a WAF/anti-bot challenge page. Detect, never solve.

    Conservative by design: a false positive (treating a normal page as a challenge)
    is unacceptable, a false negative is acceptable. Every known normal fixture must
    return ``False``.
    """
    if isinstance(body, (bytes, bytearray)):
        text = bytes(body).decode("utf-8", "replace")
    elif isinstance(body, str):
        text = body
    else:
        return False

    lowered = text.lower()
    if any(marker in lowered for marker in _CHALLENGE_MARKERS):
        return True
    if "acw_sc" in lowered and any(marker in lowered for marker in _HTML_MARKERS):
        return True
    return False
