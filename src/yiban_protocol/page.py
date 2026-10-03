"""Authorize page parsing (SPEC §2.1).

Two things are lifted out of the OAuth authorize page:

* ``var page_use = '<token>';`` — a one-shot page token that later travels as the
  ``ajax_sign`` query parameter of the usersure request;
* the hidden ``<input id="key" ...>`` whose ``value`` holds a multi-line RSA public
  key in PEM form. Upstream writes ``type="test"`` on that input, so the element is
  located strictly by ``id="key"`` — never by ``type``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .errors import ParseError

_PAGE_USE_RE = re.compile(r"""var\s+page_use\s*=\s*['"]([A-Za-z0-9]+)['"]""")
_KEY_INPUT_RE = re.compile(r"""<input\b[^>]*\bid\s*=\s*['"]key['"][^>]*>""", re.IGNORECASE | re.DOTALL)
_VALUE_ATTR_RE = re.compile(r"""\bvalue\s*=\s*['"](.*?)['"]""", re.DOTALL)


@dataclass(frozen=True)
class AuthorizePage:
    """Values extracted from an OAuth authorize page."""

    page_use: str
    public_key_pem: str


def _normalize_pem(raw: str) -> str:
    """Collapse a PEM blob embedded in an HTML attribute to canonical single-fold form.

    Header/footer lines are kept, intermediate base64 lines are joined with ``\\n``,
    and surrounding whitespace/CRLF is removed.
    """
    lines = [line.strip() for line in raw.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    return "\n".join(line for line in lines if line)


def parse_authorize_page(html: str) -> AuthorizePage:
    """Parse the authorize page HTML into an :class:`AuthorizePage`.

    Raises:
        ParseError: if the ``page_use`` token or the ``id="key"`` public key input
            cannot be found.
    """
    if isinstance(html, (bytes, bytearray)):
        html = bytes(html).decode("utf-8", "replace")
    if not isinstance(html, str):
        raise ParseError("page_use", html)

    page_use_match = _PAGE_USE_RE.search(html)
    if page_use_match is None or not page_use_match.group(1):
        raise ParseError("page_use", html)

    key_input_match = _KEY_INPUT_RE.search(html)
    if key_input_match is None:
        raise ParseError("public_key", html)

    value_match = _VALUE_ATTR_RE.search(key_input_match.group(0))
    if value_match is None:
        raise ParseError("public_key", key_input_match.group(0))

    pem = _normalize_pem(value_match.group(1))
    if "-----BEGIN PUBLIC KEY-----" not in pem or "-----END PUBLIC KEY-----" not in pem:
        raise ParseError("public_key", pem)

    return AuthorizePage(page_use=page_use_match.group(1), public_key_pem=pem)
