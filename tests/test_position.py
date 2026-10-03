"""SPEC §5 row ``签到点``."""

from __future__ import annotations

import copy

import pytest

from yiban_protocol import ParseError, parse_sign_position


@pytest.fixture()
def position_data(read_fixture_json):
    return copy.deepcopy(read_fixture_json("sign_position.json")["data"])


def test_fixture_has_two_positions(position_data):
    assert len(parse_sign_position(position_data).positions) == 2


def test_first_position_fields(position_data):
    pos = parse_sign_position(position_data).positions[0]
    assert pos.id == "27464ed31464763a6827816a0ac9c8ab"
    assert pos.type == "campus"
    assert pos.title == "示例省示例市示例区示例大学示例校区-示例苑·公共教学组团"
    assert pos.address == pos.title
    assert pos.lnglat == (118.101837, 32.003954)
    assert pos.range_m == 70
    assert pos.map_type == 2
    assert pos.building_id is None
    assert pos.address_name == "自定义多边形"


def test_second_position_is_kept(position_data):
    positions = parse_sign_position(position_data).positions
    assert positions[1].id == "519c864f4cb663758c864724dd7b178c"
    assert positions[1].range_m == 110
    assert positions[1].lnglat == (118.103894, 32.007838)


def test_points_are_all_tuples(position_data):
    for pos in parse_sign_position(position_data).positions:
        assert pos.points
        for point in pos.points:
            assert isinstance(point, tuple)
            assert len(point) == 2
            assert all(isinstance(value, float) for value in point)
    assert len(parse_sign_position(position_data).positions[0].points) == 13


def test_config_scalar_fields(position_data):
    config = parse_sign_position(position_data)
    assert config.state == 0
    assert config.msg == ""
    assert config.acs_state == "off"
    assert config.out_state == "on"
    assert config.type_ == "campus"
    assert config.remark.startswith("因受不可抗因素影响")
    assert config.file_url == ""
    assert config.attachment_file_name == ""
    assert isinstance(config.is_need_photo, bool)
    # The top-level Range is the sign-in time window object, not a radius.
    assert config.range_m is None


def test_string_numeric_range_is_coerced(position_data):
    position_data["Position"][0]["Range"] = "110"
    assert parse_sign_position(position_data).positions[0].range_m == 110


def test_literal_none_building_id_becomes_none(position_data):
    position_data["Position"][0]["BuildingId"] = "None"
    assert parse_sign_position(position_data).positions[0].building_id is None


def test_empty_string_building_id_becomes_none(position_data):
    position_data["Position"][0]["BuildingId"] = ""
    assert parse_sign_position(position_data).positions[0].building_id is None


def test_bool_forms_are_coerced(position_data):
    position_data["IsNeedPhoto"] = "1"
    assert parse_sign_position(position_data).is_need_photo is True
    position_data["IsNeedPhoto"] = "0"
    assert parse_sign_position(position_data).is_need_photo is False
    position_data["IsNeedPhoto"] = False
    assert parse_sign_position(position_data).is_need_photo is False


def test_missing_position_key_raises(position_data):
    del position_data["Position"]
    with pytest.raises(ParseError) as excinfo:
        parse_sign_position(position_data)
    assert excinfo.value.field == "Position"


def test_empty_position_list_is_valid(position_data):
    position_data["Position"] = []
    assert parse_sign_position(position_data).positions == []


def test_malformed_lnglat_raises(position_data):
    position_data["Position"][0]["LngLat"] = "not-a-coordinate"
    with pytest.raises(ParseError) as excinfo:
        parse_sign_position(position_data)
    assert excinfo.value.field == "LngLat"


def test_missing_position_mandatory_key_raises(position_data):
    del position_data["Position"][0]["Title"]
    with pytest.raises(ParseError):
        parse_sign_position(position_data)


def test_missing_points_defaults_to_empty_list(position_data):
    del position_data["Position"][0]["Points"]
    assert parse_sign_position(position_data).positions[0].points == []
