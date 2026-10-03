"""Identity parsing for ``base/c/auth/yiban`` responses (SPEC §2.4).

Input is the ``data`` object of the auth envelope. The five person/university
fields are mandatory; ``State`` is coerced numerically (§3.1); ``Container``
defaults to ``"StudentDefault"``; ``Apps`` missing means an empty list.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .errors import ParseError

_DEFAULT_CONTAINER = "StudentDefault"
_REQUIRED_APP_KEYS = ("Id", "ServiceId", "AppName", "AppUrl")


@dataclass(frozen=True)
class App:
    """One app entry from the identity payload."""

    id: str
    service_id: str
    name: str
    url: str
    auth_code: str


@dataclass(frozen=True)
class Identity:
    """Identity payload from ``base/c/auth/yiban``."""

    university_name: str
    university_id: str
    person_id: str
    person_name: str
    person_type: str
    state: int
    container: str
    apps: list[App]


def _required_str(data: dict, key: str, field_name: str) -> str:
    if key not in data or data[key] is None:
        raise ParseError(field_name, data.get(key))
    value = data[key]
    if not isinstance(value, str):
        raise ParseError(field_name, value)
    return value


def _to_int(value: Any) -> int | None:
    """Coerce a dual-state upstream number (int/float or numeric string) to int."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return int(text)
        except ValueError:
            try:
                return int(float(text))
            except ValueError:
                return None
    return None


def _parse_app(item: Any) -> App:
    if not isinstance(item, dict):
        raise ParseError("Apps", item)
    for key in _REQUIRED_APP_KEYS:
        if key not in item or item[key] is None:
            raise ParseError(f"Apps[].{key}", item)

    auth_code = item.get("AuthCode")
    if auth_code is None:
        auth_code = ""
    elif not isinstance(auth_code, str):
        auth_code = str(auth_code)

    return App(
        id=str(item["Id"]),
        service_id=str(item["ServiceId"]),
        name=str(item["AppName"]),
        url=str(item["AppUrl"]),
        auth_code=auth_code,
    )


def parse_identity(data: dict) -> Identity:
    """Parse the ``data`` object of a ``base/c/auth/yiban`` response.

    Raises:
        ParseError: if a mandatory field is missing, or ``Apps`` is not a list.
    """
    if not isinstance(data, dict):
        raise ParseError("identity", data)

    container_raw = data.get("Container")
    if isinstance(container_raw, str) and container_raw:
        container = container_raw
    elif container_raw is None or container_raw == "":
        container = _DEFAULT_CONTAINER
    else:
        container = str(container_raw)

    apps_raw = data.get("Apps")
    if apps_raw is None:
        apps = []
    elif isinstance(apps_raw, list):
        apps = [_parse_app(item) for item in apps_raw]
    else:
        raise ParseError("Apps", apps_raw)

    return Identity(
        university_name=_required_str(data, "UniversityName", "UniversityName"),
        university_id=_required_str(data, "UniversityId", "UniversityId"),
        person_id=_required_str(data, "PersonId", "PersonId"),
        person_name=_required_str(data, "PersonName", "PersonName"),
        person_type=_required_str(data, "PersonType", "PersonType"),
        state=_to_int(data.get("State")),
        container=container,
        apps=apps,
    )
