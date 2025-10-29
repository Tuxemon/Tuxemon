# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest

from tuxemon.db import Direction
from tuxemon.map.map_region import (
    PushEffect,
    RegionProperties,
    direction_to_list,
    extract_region_properties,
)


class TestExtractRegionProperties(unittest.TestCase):
    def test_empty_properties(self):
        self.assertIsNone(extract_region_properties({}))

    def test_only_enter_from(self):
        properties = {"enter_from": "up, left"}
        expected = RegionProperties(
            enter_from=[Direction.left, Direction.up],
            exit_from=[],
            endure=[],
            entity=None,
            key=None,
        )
        self.assertEqual(extract_region_properties(properties), expected)

    def test_only_exit_from(self):
        properties = {"exit_from": "down"}
        expected = RegionProperties(
            enter_from=[Direction.up, Direction.left, Direction.right],
            exit_from=[Direction.down],
            endure=[],
            entity=None,
            key=None,
        )
        self.assertEqual(extract_region_properties(properties), expected)

    def test_all_properties(self):
        properties = {
            "enter_from": "up, left",
            "exit_from": "down, right",
            "endure": "left",
            "key": "door",
        }
        expected = RegionProperties(
            enter_from=[Direction.left, Direction.up],
            exit_from=[Direction.down, Direction.right],
            endure=[Direction.left],
            entity=None,
            key="door",
        )
        self.assertEqual(extract_region_properties(properties), expected)

    def test_slide_label(self):
        properties = {"key": "slide"}
        expected = RegionProperties(
            enter_from=list(Direction),
            exit_from=list(Direction),
            endure=list(Direction),
            entity=None,
            key="slide",
        )
        self.assertEqual(extract_region_properties(properties), expected)

    def test_invalid_direction(self):
        properties = {"enter_from": "up, invalid"}
        with self.assertRaises(ValueError):
            extract_region_properties(properties)

    def test_none_value(self):
        properties = {"enter_from": None}
        expected = RegionProperties(
            enter_from=[], exit_from=[], endure=[], entity=None, key=None
        )
        self.assertEqual(extract_region_properties(properties), expected)

    def test_duplicate_directions(self):
        properties = {"enter_from": "up, up, left"}
        expected = RegionProperties(
            enter_from=[Direction.left, Direction.up],
            exit_from=[],
            endure=[],
            entity=None,
            key=None,
        )
        self.assertEqual(extract_region_properties(properties), expected)

    def test_mixed_case_directions(self):
        properties = {"enter_from": "Up, Left"}
        expected = RegionProperties(
            enter_from=[Direction.left, Direction.up],
            exit_from=[],
            endure=[],
            entity=None,
            key=None,
        )
        self.assertEqual(extract_region_properties(properties), expected)

    def test_extra_whitespace(self):
        properties = {"enter_from": " up , left "}
        expected = RegionProperties(
            enter_from=[Direction.left, Direction.up],
            exit_from=[],
            endure=[],
            entity=None,
            key=None,
        )
        self.assertEqual(extract_region_properties(properties), expected)

    def test_invalid_key(self):
        properties = {"invalid_key": "value"}
        self.assertIsNone(extract_region_properties(properties))

    def test_empty_string_values(self):
        properties = {"enter_from": "", "exit_from": ""}
        with self.assertRaises(ValueError):
            extract_region_properties(properties)

    def test_missing_enter_exit_from(self):
        properties = {"endure": "left"}
        expected = RegionProperties(
            enter_from=[],
            exit_from=[],
            endure=[Direction.left],
            entity=None,
            key=None,
        )
        self.assertEqual(extract_region_properties(properties), expected)

    def test_invalid_slide_label(self):
        properties = {"enter_from": "slide"}
        with self.assertRaises(ValueError):
            extract_region_properties(properties)

    def test_mixed_valid_invalid_keys(self):
        properties = {
            "enter_from": "up, left",
            "invalid_key": "value",
            "key": "door",
        }
        expected = RegionProperties(
            enter_from=[Direction.left, Direction.up],
            exit_from=[],
            endure=[],
            entity=None,
            key="door",
        )
        self.assertEqual(extract_region_properties(properties), expected)

    def test_empty_endure(self):
        properties = {"endure": ""}
        with self.assertRaises(ValueError):
            extract_region_properties(properties)

    def test_circular_logic(self):
        properties = {"exit_from": "left, right"}
        expected = RegionProperties(
            enter_from=[Direction.up, Direction.down],
            exit_from=[Direction.left, Direction.right],
            endure=[],
            entity=None,
            key=None,
        )
        self.assertEqual(extract_region_properties(properties), expected)

    def test_all_keys_missing(self):
        properties = {"unknown_key": "value"}
        self.assertIsNone(extract_region_properties(properties))

    def test_case_insensitive_keys(self):
        properties = {"Enter_from": "up, left"}
        expected = RegionProperties(
            enter_from=[Direction.left, Direction.up],
            exit_from=[],
            endure=[],
            entity=None,
            key=None,
        )
        self.assertEqual(extract_region_properties(properties), expected)

    def test_all_directions_empty_key(self):
        properties = {"enter_from": "up, down, left, right", "key": ""}
        with self.assertRaises(ValueError):
            extract_region_properties(properties)

    def test_invalid_characters_in_directions(self):
        properties = {"enter_from": "up, @, left"}
        with self.assertRaises(ValueError):
            extract_region_properties(properties)

    def test_push_tile_valid(self):
        properties = {
            "key": "push_tile",
            "push_direction": "right",
            "push_strength": "2",
        }
        expected = RegionProperties(
            enter_from=list(Direction),
            exit_from=list(Direction),
            endure=[],
            entity=None,
            key="push_tile",
            push_effect=PushEffect(Direction.right, 2),
            speed_modifier=None,
        )
        self.assertEqual(extract_region_properties(properties), expected)

    def test_push_tile_missing_strength(self):
        properties = {"key": "push_tile", "push_direction": "left"}
        with self.assertRaises(ValueError):
            extract_region_properties(properties)

    def test_push_tile_zero_strength(self):
        properties = {
            "key": "push_tile",
            "push_direction": "up",
            "push_strength": "0",
        }
        with self.assertRaises(ValueError):
            extract_region_properties(properties)

    def test_push_tile_invalid_direction(self):
        properties = {
            "key": "push_tile",
            "push_direction": "banana",
            "push_strength": "3",
        }
        with self.assertRaises(ValueError):
            extract_region_properties(properties)

    def test_slide_with_speed_modifier(self):
        properties = {"key": "slide", "speed_modifier": "1.5"}
        expected = RegionProperties(
            enter_from=list(Direction),
            exit_from=list(Direction),
            endure=list(Direction),
            entity=None,
            key="slide",
            push_effect=None,
            speed_modifier=1.5,
        )
        self.assertEqual(extract_region_properties(properties), expected)

    def test_invalid_speed_modifier(self):
        properties = {"speed_modifier": "fast"}
        with self.assertRaises(ValueError):
            extract_region_properties(properties)

    def test_push_tile_with_speed_modifier(self):
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
            entity=None,
            key="push_tile",
            push_effect=PushEffect(Direction.down, 4),
            speed_modifier=0.75,
        )
        self.assertEqual(extract_region_properties(properties), expected)

    def test_push_strength_as_int(self):
        properties = {
            "key": "push_tile",
            "push_direction": "up",
            "push_strength": 3,
        }
        expected = RegionProperties(
            enter_from=list(Direction),
            exit_from=list(Direction),
            endure=[],
            entity=None,
            key="push_tile",
            push_effect=PushEffect(Direction.up, 3),
            speed_modifier=None,
        )
        self.assertEqual(extract_region_properties(properties), expected)

    def test_push_strength_invalid_string(self):
        properties = {
            "key": "push_tile",
            "push_direction": "right",
            "push_strength": "strong",
        }
        with self.assertRaises(ValueError):
            extract_region_properties(properties)

    def test_slide_with_unknown_keys(self):
        properties = {
            "key": "slide",
            "speed_modifier": "1.2",
            "unknown": "value",
        }
        expected = RegionProperties(
            enter_from=list(Direction),
            exit_from=list(Direction),
            endure=list(Direction),
            entity=None,
            key="slide",
            push_effect=None,
            speed_modifier=1.2,
        )
        self.assertEqual(extract_region_properties(properties), expected)

    def test_push_tile_defaults_when_enter_exit_missing(self):
        properties = {
            "key": "push_tile",
            "push_direction": "up",
            "push_strength": "1",
        }
        expected = RegionProperties(
            enter_from=list(Direction),
            exit_from=list(Direction),
            endure=[],
            entity=None,
            key="push_tile",
            push_effect=PushEffect(Direction.up, 1),
            speed_modifier=None,
        )
        self.assertEqual(extract_region_properties(properties), expected)


class TestDirectionToList(unittest.TestCase):
    def test_empty_string_with_whitespace(self):
        with self.assertRaises(ValueError):
            direction_to_list("    ")

    def test_empty_string(self):
        with self.assertRaises(ValueError):
            direction_to_list("")

    def test_single_direction(self):
        result = direction_to_list("up")
        self.assertEqual(result, [Direction.up])

    def test_multiple_direction(self):
        result = direction_to_list("up,down,right")
        self.assertEqual(len(result), 3)

    def test_single_direction_with_whitespace(self):
        result = direction_to_list("   up    ")
        self.assertEqual(len(result), 1)

    def test_mutiple_direction_with_whitespace(self):
        result = direction_to_list("up   ,down  ,   right")
        self.assertEqual(len(result), 3)

    def test_repeated_directions(self):
        result = direction_to_list("up,up,down,down")
        self.assertEqual(len(result), 2)

    def test_insensitive_duplicates(self):
        result = direction_to_list("uP,dOWn")
        self.assertEqual(len(result), 2)

    def test_none_input(self):
        result = direction_to_list(None)
        self.assertEqual(result, [])

    def test_very_long_string(self):
        long_string = ",".join(["up"] * 100)
        result = direction_to_list(long_string)
        self.assertEqual(result, [Direction.up])

    def test_unicode_characters(self):
        with self.assertRaises(ValueError):
            direction_to_list("ä, ü, up")

    def test_invalid_direction(self):
        with self.assertRaises(ValueError):
            direction_to_list("invalid direction")
