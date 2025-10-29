# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import MagicMock

from tuxemon.map.map_manager import MapManager, MapType
from tuxemon.map.map_tuxemon import AbstractMap


class TestMapManager(unittest.TestCase):
    def setUp(self):
        self.map_manager = MapManager()

    def create_mock_map(self, map_type="town") -> MagicMock:
        map_data = MagicMock(spec=AbstractMap)
        map_data.events = ["event1", "event2"]
        map_data.inits = ["init1", "init2"]
        map_data.maps = {"map1": "data1", "map2": "data2"}
        map_data.slug = "map_slug"
        map_data.name = "map_name"
        map_data.description = "map_description"
        map_data.inside = True
        map_data.size = (10, 20)
        map_data.map_type = map_type
        map_data.north_trans = "north"
        map_data.south_trans = "south"
        map_data.east_trans = "east"
        map_data.west_trans = "west"
        map_data.collision_lines_map = set()
        map_data.surface_map = {}
        map_data.collision_map = {}
        map_data.filename = "map_filename"
        return map_data

    def test_init(self):
        expected_values = {
            "events": [],
            "inits": [],
            "current_map": None,
            "maps": {},
            "map_slug": "",
            "map_name": "Unknown Location",
            "map_desc": "",
            "map_inside": False,
            "map_size": (0, 0),
            "map_type": MapType(),
            "map_north": "",
            "map_south": "",
            "map_east": "",
            "map_west": "",
        }
        for attr, expected in expected_values.items():
            with self.subTest(attr=attr):
                self.assertEqual(getattr(self.map_manager, attr), expected)

    def test_load_map(self):
        map_data = self.create_mock_map()
        self.map_manager.load_map(map_data)

        self.assertEqual(self.map_manager.current_map, map_data)
        self.assertEqual(self.map_manager.events, map_data.events)
        self.assertEqual(self.map_manager.inits, map_data.inits)
        self.assertEqual(self.map_manager.maps, map_data.maps)
        self.assertEqual(self.map_manager.map_slug, map_data.slug)
        self.assertEqual(self.map_manager.map_name, map_data.name)
        self.assertEqual(self.map_manager.map_desc, map_data.description)
        self.assertTrue(self.map_manager.map_inside)
        self.assertEqual(self.map_manager.map_size, map_data.size)
        self.assertEqual(self.map_manager.map_type, MapType(name="town"))
        self.assertEqual(self.map_manager.map_north, map_data.north_trans)
        self.assertEqual(self.map_manager.map_south, map_data.south_trans)
        self.assertEqual(self.map_manager.map_east, map_data.east_trans)
        self.assertEqual(self.map_manager.map_west, map_data.west_trans)
        self.assertEqual(
            self.map_manager.collision_lines_map, map_data.collision_lines_map
        )
        self.assertEqual(self.map_manager.surface_map, map_data.surface_map)
        self.assertEqual(
            self.map_manager.collision_map, map_data.collision_map
        )

    def test_load_map_with_invalid_map_type(self):
        map_data = self.create_mock_map(map_type="unknown_type")
        self.map_manager.load_map(map_data)
        self.assertEqual(self.map_manager.map_type.name, "notype")

    def test_is_in_location_type(self):
        map_data = self.create_mock_map(map_type="town")
        self.map_manager.load_map(map_data)
        self.assertTrue(self.map_manager.is_in_location_type("town"))
        self.assertFalse(self.map_manager.is_in_location_type("shop"))

    def test_get_map_filepath(self):
        self.assertIsNone(self.map_manager.get_map_filepath())
        map_data = self.create_mock_map()
        self.map_manager.current_map = map_data
        self.assertEqual(
            self.map_manager.get_map_filepath(), map_data.filename
        )

    def test_map_type_property_logs_warning_for_invalid_type(self):
        map_data = self.create_mock_map(map_type="invalid")
        with self.assertLogs("tuxemon.map.map_manager", level="WARNING") as cm:
            self.map_manager.load_map(map_data)
            _ = self.map_manager.map_type
        self.assertTrue(any("Invalid map type" in msg for msg in cm.output))

    def test_map_type_with_none_slug(self):
        self.map_manager._map_type_slug = None
        self.assertEqual(self.map_manager.map_type.name, "notype")

    def test_map_type_with_valid_slug_no_map(self):
        self.map_manager._map_type_slug = "town"
        self.assertEqual(self.map_manager.map_type.name, "town")

    def test_map_type_with_invalid_slug(self):
        self.map_manager._map_type_slug = "unknown"
        self.assertEqual(self.map_manager.map_type.name, "notype")

    def test_collision_lines_map_without_map(self):
        self.assertEqual(self.map_manager.collision_lines_map, set())

    def test_surface_map_without_map(self):
        self.assertEqual(self.map_manager.surface_map, {})

    def test_collision_map_without_map(self):
        self.assertEqual(self.map_manager.collision_map, {})

    def test_directional_properties_without_map(self):
        self.assertEqual(self.map_manager.map_north, "")
        self.assertEqual(self.map_manager.map_south, "")
        self.assertEqual(self.map_manager.map_east, "")
        self.assertEqual(self.map_manager.map_west, "")
