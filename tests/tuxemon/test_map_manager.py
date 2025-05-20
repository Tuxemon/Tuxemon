# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import MagicMock

from tuxemon.map import TuxemonMap
from tuxemon.map_manager import MapManager, MapType


class TestMapManager(unittest.TestCase):
    def setUp(self):
        self.map_manager = MapManager()

    def test_init(self):
        self.assertEqual(self.map_manager.events, [])
        self.assertEqual(self.map_manager.inits, [])
        self.assertIsNone(self.map_manager.current_map)
        self.assertEqual(self.map_manager.maps, {})
        self.assertEqual(self.map_manager.map_slug, "")
        self.assertEqual(self.map_manager.map_name, "")
        self.assertEqual(self.map_manager.map_desc, "")
        self.assertFalse(self.map_manager.map_inside)
        self.assertEqual(self.map_manager.map_size, (0, 0))
        self.assertEqual(self.map_manager.map_type, MapType())
        self.assertEqual(self.map_manager.map_north, "")
        self.assertEqual(self.map_manager.map_south, "")
        self.assertEqual(self.map_manager.map_east, "")
        self.assertEqual(self.map_manager.map_west, "")

    def test_load_map(self):

        map_data = MagicMock(spec=TuxemonMap)
        map_data.events = ["event1", "event2"]
        map_data.inits = ["init1", "init2"]
        map_data.maps = {"map1": "data1", "map2": "data2"}
        map_data.slug = "map_slug"
        map_data.name = "map_name"
        map_data.description = "map_description"
        map_data.inside = True
        map_data.size = (10, 20)
        map_data.map_type = "town"
        map_data.north_trans = "north"
        map_data.south_trans = "south"
        map_data.east_trans = "east"
        map_data.west_trans = "west"
        map_data.collision_lines_map = set()
        map_data.surface_map = {}
        map_data.collision_map = {}

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

    def test_get_map_filepath(self):
        self.assertIsNone(self.map_manager.get_map_filepath())
        map_data = MagicMock(spec=TuxemonMap)
        map_data.filename = "map_filename"
        self.map_manager.current_map = map_data
        self.assertEqual(
            self.map_manager.get_map_filepath(), map_data.filename
        )
