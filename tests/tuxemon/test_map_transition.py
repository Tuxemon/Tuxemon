# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import MagicMock

from tuxemon.map.transition import MapTransition


class TestMapTransition(unittest.TestCase):

    def setUp(self):
        self.map_loader = MagicMock()
        self.npc_manager = MagicMock()
        self.map_manager = MagicMock()
        self.boundary = MagicMock()
        self.event_engine = MagicMock()
        self.map_transition = MapTransition(
            self.map_loader,
            self.npc_manager,
            self.map_manager,
            self.boundary,
            self.event_engine,
        )

    def test_init(self):
        self.assertEqual(self.map_transition.map_loader, self.map_loader)
        self.assertEqual(self.map_transition.map_manager, self.map_manager)
        self.assertEqual(self.map_transition.npc_manager, self.npc_manager)
        self.assertEqual(self.map_transition.boundary, self.boundary)
        self.assertEqual(self.map_transition.event_engine, self.event_engine)

    def test_change_map(self):
        map_name = "test_map"
        map_data = MagicMock()
        self.map_loader.load_map_data.return_value = map_data
        self.map_transition.change_map(map_name)
        self.map_loader.load_map_data.assert_called_once_with(map_name)
        self.event_engine.reset.assert_called_once()
        self.event_engine.set_current_map.assert_called_once_with(map_data)
        self.map_manager.load_map.assert_called_once_with(map_data)
        self.npc_manager.clear_npcs.assert_called_once()
        self.boundary.update_boundaries.assert_called_once()

    def test_reset_events(self):
        map_data = MagicMock()
        self.map_transition._reset_events(map_data)
        self.event_engine.reset.assert_called_once()
        self.event_engine.set_current_map.assert_called_once_with(map_data)

    def test_update_map_state(self):
        map_data = MagicMock()
        self.map_transition._update_map_state(map_data)
        self.map_manager.load_map.assert_called_once_with(map_data)

    def test_clear_npcs(self):
        self.map_transition._clear_npcs()
        self.npc_manager.clear_npcs.assert_called_once()

    def test_update_boundaries(self):
        self.map_manager.map_size = (10, 10)
        self.map_transition._update_boundaries()
        self.boundary.update_boundaries.assert_called_once_with((10, 10))
