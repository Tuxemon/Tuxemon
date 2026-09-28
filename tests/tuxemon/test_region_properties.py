# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import pytest

from tuxemon.db import Direction
from tuxemon.map.region import (
    PushEffect,
    RegionProperties,
    direction_to_list,
    extract_region_properties,
)


def test_empty_properties():
    assert extract_region_properties({}) is None


@pytest.mark.parametrize(
    "properties, expected",
    [
        pytest.param(
            {"enter_from": "up, left"},
            RegionProperties(
                enter_from=[Direction.UP, Direction.LEFT],
                exit_from=[],
                endure=[],
                key=None,
            ),
            id="enter_from_basic",
        ),
        pytest.param(
            {"exit_from": "down"},
            RegionProperties(
                enter_from=[Direction.UP, Direction.LEFT, Direction.RIGHT],
                exit_from=[Direction.DOWN],
                endure=[],
                key=None,
            ),
            id="exit_from_basic",
        ),
        pytest.param(
            {
                "enter_from": "up, left",
                "exit_from": "down, right",
                "endure": "left",
                "key": "door",
            },
            RegionProperties(
                enter_from=[Direction.UP, Direction.LEFT],
                exit_from=[Direction.DOWN, Direction.RIGHT],
                endure=[Direction.LEFT],
                key="door",
            ),
            id="all_fields",
        ),
        pytest.param(
            {"key": "slide"},
            RegionProperties(
                enter_from=list(Direction),
                exit_from=list(Direction),
                endure=list(Direction),
                key="slide",
            ),
            id="key_only_defaults",
        ),
        pytest.param(
            {"enter_from": None},
            RegionProperties(
                enter_from=[],
                exit_from=[],
                endure=[],
                key=None,
            ),
            id="enter_from_none",
        ),
        pytest.param(
            {"enter_from": "up, up, left"},
            RegionProperties(
                enter_from=[Direction.UP, Direction.LEFT],
                exit_from=[],
                endure=[],
                key=None,
            ),
            id="dedupe_values",
        ),
        pytest.param(
            {"enter_from": "Up, Left"},
            RegionProperties(
                enter_from=[Direction.UP, Direction.LEFT],
                exit_from=[],
                endure=[],
                key=None,
            ),
            id="case_insensitive",
        ),
        pytest.param(
            {"enter_from": " up , left "},
            RegionProperties(
                enter_from=[Direction.UP, Direction.LEFT],
                exit_from=[],
                endure=[],
                key=None,
            ),
            id="strip_whitespace",
        ),
        pytest.param(
            {"endure": "left"},
            RegionProperties(
                enter_from=[],
                exit_from=[],
                endure=[Direction.LEFT],
                key=None,
            ),
            id="endure_only",
        ),
        pytest.param(
            {"Enter_from": "up, left"},
            RegionProperties(
                enter_from=[Direction.UP, Direction.LEFT],
                exit_from=[],
                endure=[],
                key=None,
            ),
            id="case_insensitive_key",
        ),
        pytest.param(
            {"exit_from": "left, right"},
            RegionProperties(
                enter_from=[Direction.UP, Direction.DOWN],
                exit_from=[Direction.LEFT, Direction.RIGHT],
                endure=[],
                key=None,
            ),
            id="exit_from_multiple",
        ),
    ],
)
def test_extract_region_properties_valid(properties, expected):
    assert extract_region_properties(properties) == expected


@pytest.mark.parametrize(
    "properties",
    [
        pytest.param({"enter_from": "up, invalid"}, id="invalid_direction"),
        pytest.param({"enter_from": ""}, id="empty_enter_from"),
        pytest.param({"exit_from": ""}, id="empty_exit_from"),
        pytest.param({"enter_from": "slide"}, id="invalid_slide_usage"),
        pytest.param({"enter_from": "up, @, left"}, id="invalid_symbol"),
        pytest.param({"enter_from": "up", "key": ""}, id="empty_key"),
        pytest.param({"speed_modifier": "fast"}, id="unknown_property"),
        pytest.param(
            {"key": "push_tile", "push_direction": "left"},
            id="push_tile_missing_strength",
        ),
        pytest.param(
            {"key": "push_tile", "push_direction": "up", "push_strength": "0"},
            id="push_tile_strength_zero",
        ),
        pytest.param(
            {
                "key": "push_tile",
                "push_direction": "banana",
                "push_strength": "3",
            },
            id="push_tile_invalid_direction",
        ),
        pytest.param(
            {
                "key": "push_tile",
                "push_direction": "right",
                "push_strength": "strong",
            },
            id="push_tile_invalid_strength",
        ),
    ],
)
def test_extract_region_properties_invalid(properties):
    with pytest.raises(ValueError):
        extract_region_properties(properties)


def test_extract_region_properties_invalid_key():
    assert extract_region_properties({"invalid_key": "value"}) is None


def test_extract_region_properties_all_keys_missing():
    assert extract_region_properties({"unknown_key": "value"}) is None


def test_extract_region_properties_mixed_valid_invalid_keys():
    properties = {
        "enter_from": "up, left",
        "invalid_key": "value",
        "key": "door",
    }
    expected = RegionProperties(
        enter_from=[Direction.UP, Direction.LEFT],
        exit_from=[],
        endure=[],
        key="door",
    )
    assert extract_region_properties(properties) == expected


def test_push_tile_valid():
    properties = {
        "key": "push_tile",
        "push_direction": "right",
        "push_strength": "2",
    }
    expected = RegionProperties(
        enter_from=list(Direction),
        exit_from=list(Direction),
        endure=[],
        key="push_tile",
        push_effect=PushEffect(Direction.RIGHT, 2),
        speed_modifier=None,
    )
    assert extract_region_properties(properties) == expected


def test_push_tile_with_speed_modifier():
    properties = {
        "key": "push_tile",
        "push_direction": "down",
        "push_strength": "4",
        "speed_modifier": "0.75",
    }
    expected = RegionProperties(
        enter_from=list(Direction),
        exit_from=list(Direction),
        endure=[],
        key="push_tile",
        push_effect=PushEffect(Direction.DOWN, 4),
        speed_modifier=0.75,
    )
    assert extract_region_properties(properties) == expected


def test_push_strength_as_int():
    properties = {
        "key": "push_tile",
        "push_direction": "up",
        "push_strength": 3,
    }
    expected = RegionProperties(
        enter_from=list(Direction),
        exit_from=list(Direction),
        endure=[],
        key="push_tile",
        push_effect=PushEffect(Direction.UP, 3),
        speed_modifier=None,
    )
    assert extract_region_properties(properties) == expected


def test_slide_with_speed_modifier():
    properties = {"key": "slide", "speed_modifier": "1.5"}
    expected = RegionProperties(
        enter_from=list(Direction),
        exit_from=list(Direction),
        endure=list(Direction),
        key="slide",
        push_effect=None,
        speed_modifier=1.5,
    )
    assert extract_region_properties(properties) == expected


def test_slide_with_unknown_keys():
    properties = {"key": "slide", "speed_modifier": "1.2", "unknown": "value"}
    expected = RegionProperties(
        enter_from=list(Direction),
        exit_from=list(Direction),
        endure=list(Direction),
        key="slide",
        push_effect=None,
        speed_modifier=1.2,
    )
    assert extract_region_properties(properties) == expected


@pytest.mark.parametrize(
    "value",
    [
        pytest.param("", id="empty_string"),
        pytest.param("   ", id="whitespace_only"),
    ],
)
def test_direction_to_list_empty(value):
    with pytest.raises(ValueError):
        direction_to_list(value)


def test_direction_to_list_single():
    assert direction_to_list("up") == [Direction.UP]


def test_direction_to_list_multiple():
    result = direction_to_list("up,down,right")
    assert set(result) == {Direction.UP, Direction.DOWN, Direction.RIGHT}


def test_direction_to_list_whitespace():
    assert direction_to_list("   up    ") == [Direction.UP]


def test_direction_to_list_multiple_whitespace():
    result = direction_to_list("up   ,down  ,   right")
    assert set(result) == {Direction.UP, Direction.DOWN, Direction.RIGHT}


def test_direction_to_list_repeated():
    result = direction_to_list("up,up,down,down")
    assert set(result) == {Direction.UP, Direction.DOWN}


def test_direction_to_list_case_insensitive():
    result = direction_to_list("uP,dOWn")
    assert set(result) == {Direction.UP, Direction.DOWN}


def test_direction_to_list_none():
    assert direction_to_list(None) == []


def test_direction_to_list_long_string():
    long_string = ",".join(["up"] * 100)
    assert direction_to_list(long_string) == [Direction.UP]


def test_direction_to_list_unicode_invalid():
    with pytest.raises(ValueError):
        direction_to_list("ä, ü, up")


def test_direction_to_list_invalid():
    with pytest.raises(ValueError):
        direction_to_list("invalid direction")
