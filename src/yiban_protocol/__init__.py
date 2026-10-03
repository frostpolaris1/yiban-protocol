"""yiban-protocol — clean-room parser/builder for the Yiban web OAuth + nightAttendance chain.

Parse (bytes/dict -> structured data) and build (structured params -> request body/URL)
only. No network, no session handling, no retries, no logging, no global state.

``crypto.encrypt_password`` lives behind the optional ``[crypto]`` extra and is
exposed lazily (see :func:`__getattr__`), so importing the core package never
requires a third-party dependency.
"""

from __future__ import annotations

from typing import Any

from .envelopes import (
    Envelope,
    UsersureResult,
    looks_like_challenge,
    parse_api_envelope,
    parse_usersure_response,
)
from .errors import ParseError, SessionExpired, YibanProtocolError
from .forms import build_sign_in_body, build_usersure_form
from .identity import App, Identity, parse_identity
from .location import extract_verify_request
from .page import AuthorizePage, parse_authorize_page
from .position import Position, SignPositionConfig, parse_sign_position

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "YibanProtocolError",
    "ParseError",
    "SessionExpired",
    "AuthorizePage",
    "parse_authorize_page",
    "extract_verify_request",
    "Envelope",
    "parse_api_envelope",
    "UsersureResult",
    "parse_usersure_response",
    "looks_like_challenge",
    "App",
    "Identity",
    "parse_identity",
    "Position",
    "SignPositionConfig",
    "parse_sign_position",
    "build_usersure_form",
    "build_sign_in_body",
]


def __getattr__(name: str) -> Any:
    """Lazily expose ``encrypt_password`` without importing the optional crypto extra."""
    if name == "encrypt_password":
        from . import crypto

        return crypto.encrypt_password
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
