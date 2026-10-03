"""SPEC §5 row ``表单构造``."""

from __future__ import annotations

import json
from urllib.parse import parse_qsl

from yiban_protocol import build_sign_in_body, build_usersure_form

_SIGN_ADDRESS = "示例省示例市示例区示例大学示例校区-示例苑·公共教学组团"
_SIGN_LNGLAT = (118.101837, 32.003954)


def _pairs(body: str) -> list[tuple[str, str]]:
    parts = body.split("&")
    result = []
    for part in parts:
        key, _, value = part.partition("=")
        result.append((key, value))
    return result


def test_usersure_form_matches_fixture_field_by_field(read_fixture):
    expected = parse_qsl(read_fixture("usersure_form.txt"))
    values = dict(expected)
    built = build_usersure_form(
        values["oauth_uname"],
        values["oauth_upwd"],
        values["client_id"],
        values["redirect_uri"],
    )
    assert parse_qsl(built) == expected


def test_usersure_form_field_order(read_fixture):
    values = dict(parse_qsl(read_fixture("usersure_form.txt")))
    built = build_usersure_form(
        values["oauth_uname"], values["oauth_upwd"], values["client_id"], values["redirect_uri"]
    )
    assert [key for key, _ in parse_qsl(built)] == [
        "oauth_uname",
        "oauth_upwd",
        "client_id",
        "redirect_uri",
        "display",
    ]


def test_usersure_form_scope_only_when_requested():
    without = build_usersure_form("13800000000", "cipher", "cid", "https://example.org/cb")
    assert "scope" not in without
    with_scope = build_usersure_form(
        "13800000000", "cipher", "cid", "https://example.org/cb", scope="basic"
    )
    assert with_scope.endswith("&scope=basic")


def test_usersure_form_custom_display():
    built = build_usersure_form("13800000000", "cipher", "cid", "https://example.org/cb", display="mobile")
    assert "display=mobile" in built


def test_sign_in_body_equals_urlencoded_fixture_exactly(read_fixture):
    expected = read_fixture("sign_in_body_urlencoded.txt")
    built = build_sign_in_body(lnglat=_SIGN_LNGLAT, address=_SIGN_ADDRESS)
    assert built == expected


def test_sign_in_body_reconstructs_from_plain_fixture(read_fixture):
    expected = read_fixture("sign_in_body_urlencoded.txt")
    values = dict(_pairs(read_fixture("sign_in_body.txt")))
    sign_info = json.loads(values["SignInfo"])
    lng, lat = (float(part) for part in sign_info["LngLat"].split(","))
    built = build_sign_in_body(lnglat=(lng, lat), address=sign_info["Address"])
    assert built == expected


def test_sign_info_json_is_byte_identical():
    built = build_sign_in_body(lnglat=(118.88070060477973, 31.925291887303278), address="A")
    # Recover SignInfo by splitting on the literal separators instead of unquoting.
    raw = built.split("&SignInfo=", 1)[1].rsplit("&OutState=", 1)[0]
    from urllib.parse import unquote_plus

    assert unquote_plus(raw) == (
        '{"Reason": "", "AttachmentFileName": "", '
        '"LngLat": "118.88070060477973,31.925291887303278", "Address": "A"}'
    )


def test_sign_in_body_honours_optional_fields():
    built = build_sign_in_body(
        lnglat=(1.0, 2.0),
        address="addr",
        out_state=2,
        reason="r",
        attachment_file_name="a.jpg",
        code="c",
        phone_model="m",
    )
    assert built.startswith("Code=c&PhoneModel=m&SignInfo=")
    assert built.endswith("&OutState=2")
    from urllib.parse import unquote_plus

    sign_info = unquote_plus(built.split("&SignInfo=", 1)[1].rsplit("&OutState=", 1)[0])
    assert json.loads(sign_info)["Reason"] == "r"
    assert json.loads(sign_info)["AttachmentFileName"] == "a.jpg"
    assert json.loads(sign_info)["LngLat"] == "1.0,2.0"
