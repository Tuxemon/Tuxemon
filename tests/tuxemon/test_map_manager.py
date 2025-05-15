# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import Mock

from tuxemon.event.eventengine import EventEngine
from tuxemon.map import TuxemonMap
from tuxemon.map_manager import MapManager, MapType


class TestMapManager(unittest.TestCase):

    def test_init(self):
        event_engine = Mock(spec=EventEngine)
        map_manager = MapManager(event_engine)
        self.assertEqual(map_manager.event_engine, event_engine)
        self.assertEqual(map_manager.events, [])
        self.assertEqual(map_manager.inits, [])
        self.assertIsNone(map_manager.current_map)
        self.assertEqual(map_manager.maps, {})
        self.assertEqual(map_manager.map_slug, "")
        self.assertEqual(map_manager.map_name, "")
        self.assertEqual(map_manager.map_desc, "")
        self.assertFalse(map_manager.map_inside)
        self.assertEqual(map_manager.map_size, (0, 0))
        self.assertEqual(map_manager.map_type, MapType())
        self.assertEqual(map_manager.map_north, "")
        self.assertEqual(map_manager.map_south, "")
        self.assertEqual(map_manager.map_east, "")
        self.assertEqual(map_manager.map_west, "")

    def test_load_map(self):
        event_engine = Mock(spec=EventEngine)
        map_manager = MapManager(event_engine)

        map_data = Mock(spec=TuxemonMap)
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

        map_manager.load_map(map_data)

        self.assertEqual(map_manager.current_map, map_data)
        self.assertEqual(map_manager.events, map_data.events)
        self.assertEqual(map_manager.inits, map_data.inits)
        self.assertEqual(map_manager.maps, map_data.maps)
        self.assertEqual(map_manager.map_slug, map_data.slug)
        self.assertEqual(map_manager.map_name, map_data.name)
        self.assertEqual(map_manager.map_desc, map_data.description)
        self.assertTrue(map_manager.map_inside)
        self.assertEqual(map_manager.map_size, map_data.size)
        self.assertEqual(map_manager.map_type, MapType(name="town"))
        self.assertEqual(map_manager.map_north, map_data.north_trans)
        self.assertEqual(map_manager.map_south, map_data.south_trans)
        self.assertEqual(map_manager.map_east, map_data.east_trans)
        self.assertEqual(map_manager.map_west, map_data.west_trans)
        self.assertEqual(
            map_manager.collision_lines_map, map_data.collision_lines_map
        )
        self.assertEqual(map_manager.surface_map, map_data.surface_map)
        self.assertEqual(map_manager.collision_map, map_data.collision_map)

        event_engine.reset.assert_called_once()
        event_engine.set_current_map.assert_called_once_with(map_data)

    def test_get_map_filepath(self):
        event_engine = Mock(spec=EventEngine)
        map_manager = MapManager(event_engine)

        self.assertIsNone(map_manager.get_map_filepath())

        map_data = Mock(spec=TuxemonMap)
        map_data.filename = "map_filename"
        map_manager.current_map = map_data
        self.assertEqual(map_manager.get_map_filepath(), map_data.filename)
