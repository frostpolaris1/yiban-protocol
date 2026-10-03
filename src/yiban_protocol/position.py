"""Sign-in point parsing for ``nightAttendance .../signPosition`` (SPEC §2.5).

Input is the ``data`` object. ``Position`` is always an array — callers must not
assume a single candidate. Numeric fields arrive in either numeric or string form
and are converged per §3.1; the literal string ``"None"`` is treated as ``None``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .errors import ParseError

_REQUIRED_POSITION_KEYS = ("Id", "Type", "Title", "Address", "LngLat")


@dataclass(frozen=True)
class Position:
    """A single candidate sign-in point (exact point or campus polygon)."""

    id: str
    type: str
    title: str
    address: str
    lnglat: tuple[float, float]
    range_m: int | None
    points: list[tuple[float, float]]
    map_type: int | None
    address_name: str | None
    campus: str | None
    building_id: str | None
    create_time: str | None


@dataclass(frozen=True)
class SignPositionConfig:
    """The ``signPosition`` ``data`` object, including all candidate positions."""

    state: int | None
    msg: str
    acs_state: str | None
    out_state: str | None
    remark: str | None
    file_url: str | None
    type_: str | None
    is_need_photo: bool | None
    attachment_file_name: str | None
    range_m: int | None
    positions: list[Position]


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


def _to_bool(value: Any) -> bool | None:
    """Coerce the upstream dual-state boolean form to bool."""
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        text = value.strip().lower()
        if text in ("1", "true"):
            return True
        if text in ("0", "false"):
            return False
        try:
            return float(text) != 0
        except ValueError:
            return None
    return None


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return str(value)


def _none_like(value: Any) -> str | None:
    """The literal ``"None"`` and the empty string both mean "no value" (§3.2)."""
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
        if text == "" or text == "None":
            return None
        return value
    return str(value)


def _parse_lnglat(value: Any) -> tuple[float, float]:
    if not isinstance(value, str):
        raise ParseError("LngLat", value)
    parts = value.split(",")
    if len(parts) != 2:
        raise ParseError("LngLat", value)
    try:
        return (float(parts[0].strip()), float(parts[1].strip()))
    except ValueError as exc:
        raise ParseError("LngLat", value) from exc


def _parse_points(value: Any) -> list[tuple[float, float]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ParseError("Points", value)
    return [_parse_lnglat(item) for item in value]


def _required_str(item: dict, key: str, field_name: str) -> str:
    value = item.get(key)
    if value is None:
        raise ParseError(field_name, item)
    if not isinstance(value, str):
        raise ParseError(field_name, value)
    return value


def _parse_position(item: Any) -> Position:
    if not isinstance(item, dict):
        raise ParseError("Position", item)
    for key in _REQUIRED_POSITION_KEYS:
        if key not in item or item[key] is None:
            raise ParseError(key, item)

    return Position(
        id=_required_str(item, "Id", "Id"),
        type=_required_str(item, "Type", "Type"),
        title=_required_str(item, "Title", "Title"),
        address=_required_str(item, "Address", "Address"),
        lnglat=_parse_lnglat(item["LngLat"]),
        range_m=_to_int(item.get("Range")),
        points=_parse_points(item.get("Points")),
        map_type=_to_int(item.get("MapType")),
        address_name=_optional_str(item.get("AddressName")),
        campus=_optional_str(item.get("Campus")),
        building_id=_none_like(item.get("BuildingId")),
        create_time=_optional_str(item.get("CreateTime")),
    )


def parse_sign_position(data: dict) -> SignPositionConfig:
    """Parse the ``data`` object of a ``signPosition`` response.

    Raises:
        ParseError: if ``Position`` is missing/not a list, a candidate is missing a
            mandatory key, or an ``LngLat``/``Points`` value is malformed.
    """
    if not isinstance(data, dict):
        raise ParseError("signPosition", data)

    if "Position" not in data or data["Position"] is None:
        raise ParseError("Position", data)
    positions_raw = data["Position"]
    if not isinstance(positions_raw, list):
        raise ParseError("Position", positions_raw)

    positions = [_parse_position(item) for item in positions_raw]

    msg = data.get("Msg")
    if not isinstance(msg, str):
        msg = "" if msg is None else str(msg)

    return SignPositionConfig(
        state=_to_int(data.get("State")),
        msg=msg,
        acs_state=_optional_str(data.get("AcsState")),
        out_state=_optional_str(data.get("OutState")),
        remark=_optional_str(data.get("Remark")),
        file_url=_optional_str(data.get("FileUrl")),
        type_=_optional_str(data.get("Type")),
        is_need_photo=_to_bool(data.get("IsNeedPhoto")),
        attachment_file_name=_optional_str(data.get("AttachmentFileName")),
        range_m=_to_int(data.get("Range")),
        positions=positions,
    )
