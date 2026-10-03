"""Error taxonomy (SPEC §1).

Parsing never speculates: a structurally unknown input raises :class:`ParseError`
carrying the offending field name plus a short fragment summary (<= 120 chars).
The single exception to "return data instead of raising" is the upstream
``code == 999`` envelope, whose semantics is "the session is gone, re-authenticate" —
that raises :class:`SessionExpired`.
"""

from __future__ import annotations

from typing import Any

_FRAGMENT_LIMIT = 120


def _summarize(value: Any, limit: int = _FRAGMENT_LIMIT) -> str:
    """Render *value* as a single-line fragment, truncated to *limit* characters."""
    if isinstance(value, str):
        text = value
    else:
        try:
            text = repr(value)
        except Exception:  # pragma: no cover - hostile __repr__
            text = object.__repr__(value)
    text = text.replace("\r", "\\r").replace("\n", "\\n")
    if len(text) > limit:
        return text[:limit] + "\u2026"
    return text


class YibanProtocolError(Exception):
    """Base class for every error raised by this library."""


class ParseError(YibanProtocolError):
    """Input does not match any known upstream shape (structural failure).

    Attributes:
        field: name of the field/element that could not be parsed.
        fragment: truncated summary of the offending input.
    """

    def __init__(self, field: str, fragment: Any = "") -> None:
        self.field = field
        self.fragment = _summarize(fragment)
        detail = f" ({self.fragment})" if self.fragment else ""
        super().__init__(f"cannot parse {field!r}{detail}")


class SessionExpired(YibanProtocolError):
    """Envelope ``code == 999``: the caller must re-authenticate."""
