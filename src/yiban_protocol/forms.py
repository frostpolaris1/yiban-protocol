"""Request body/URL construction (SPEC §2.6).

Pure builders: no I/O, no session state. Output is always an
``application/x-www-form-urlencoded`` string produced with ``quote_plus``
semantics (spaces become ``+``; ``+ / =`` become ``%2B %2F %3D``).
"""

from __future__ import annotations

import json
from urllib.parse import urlencode


def build_usersure_form(
    phone: str,
    encrypted_password: str,
    client_id: str,
    redirect_uri: str,
    *,
    display: str = "authorize",
    scope: str | None = None,
) -> str:
    """Build the usersure POST body.

    Field order matches the observed flow: ``oauth_uname`` (plain phone number),
    ``oauth_upwd`` (encrypted password), ``client_id``, ``redirect_uri``,
    ``display``; ``scope`` is appended only when explicitly provided.
    """
    pairs: list[tuple[str, str]] = [
        ("oauth_uname", phone),
        ("oauth_upwd", encrypted_password),
        ("client_id", client_id),
        ("redirect_uri", redirect_uri),
        ("display", display),
    ]
    if scope is not None:
        pairs.append(("scope", scope))
    return urlencode(pairs)


def build_sign_in_body(
    *,
    lnglat: tuple[float, float],
    address: str,
    out_state: int = 1,
    reason: str = "",
    attachment_file_name: str = "",
    code: str = "",
    phone_model: str = "",
) -> str:
    """Build the nightAttendance sign-in POST body.

    The embedded ``SignInfo`` JSON is serialized byte-for-byte like the observed
    traffic: key order ``Reason, AttachmentFileName, LngLat, Address`` and
    ``json.dumps(separators=(", ", ": "), ensure_ascii=False)`` (the JSON defaults).
    The whole body is then url-encoded.
    """
    sign_info = {
        "Reason": reason,
        "AttachmentFileName": attachment_file_name,
        "LngLat": f"{lnglat[0]},{lnglat[1]}",
        "Address": address,
    }
    payload = json.dumps(sign_info, separators=(", ", ": "), ensure_ascii=False)
    return urlencode(
        [
            ("Code", code),
            ("PhoneModel", phone_model),
            ("SignInfo", payload),
            ("OutState", out_state),
        ]
    )
