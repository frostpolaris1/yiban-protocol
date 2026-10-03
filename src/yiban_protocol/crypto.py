"""Password encryption — optional add-on (SPEC §2.7).

This is the only module allowed to depend on a third-party package
(``pycryptodome``). It is intentionally *not* imported by ``yiban_protocol/__init__``
so the core package keeps a zero third-party footprint; import this module
explicitly (or use ``from yiban_protocol import encrypt_password``) after installing
the extra::

    pip install 'yiban-protocol[crypto]'
"""

from __future__ import annotations

import base64

_MISSING_DEP_MESSAGE = (
    "yiban_protocol.crypto requires the optional dependency 'pycryptodome'. "
    "Install it with: pip install 'yiban-protocol[crypto]'"
)

try:  # pragma: no cover - exercised in tests via a blocked-import test
    from Crypto.Cipher import PKCS1_v1_5
    from Crypto.PublicKey import RSA
except ImportError as exc:  # pragma: no cover
    raise ImportError(_MISSING_DEP_MESSAGE) from exc


def encrypt_password(password: str, public_key_pem: str) -> str:
    """RSA PKCS#1 v1.5 encrypt *password* with *public_key_pem*, base64-encoded.

    With the observed RSA-1024 key the ciphertext is 128 bytes, i.e. 172 base64
    characters ending in ``==``.

    Raises:
        TypeError: if either argument is not ``str``.
        ValueError: if *public_key_pem* is not a usable RSA public key.
    """
    if not isinstance(password, str):
        raise TypeError("password must be str")
    if not isinstance(public_key_pem, str):
        raise TypeError("public_key_pem must be str")

    try:
        key = RSA.import_key(public_key_pem)
    except (ValueError, IndexError, TypeError) as exc:
        raise ValueError("public_key_pem is not a valid RSA public key") from exc

    ciphertext = PKCS1_v1_5.new(key).encrypt(password.encode("utf-8"))
    return base64.b64encode(ciphertext).decode("ascii")
