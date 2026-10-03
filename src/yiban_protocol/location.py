"""Extract the ``verify_request`` token from a 302 ``Location`` header (SPEC §2.2).

The token may sit at the very end of the query string with no ``&`` after it, so
the pattern must not require a trailing separator. A missing token is *not* an
error here: the caller decides what a missing token means.
"""

from __future__ import annotations

import re

_VERIFY_REQUEST_RE = re.compile(r"verify_request=([^&]+)")


def extract_verify_request(location: str) -> str | None:
    """Return the raw ``verify_request`` token from *location*, or ``None``.

    The token is hex, so no URL-decoding is applied; the matched text is returned
    verbatim.
    """
    if not isinstance(location, str) or not location:
        return None
    match = _VERIFY_REQUEST_RE.search(location)
    if match is None:
        return None
    return match.group(1)
