# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import MagicMock

from tuxemon.map.map_transition import MapTransition


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
        self.boundary.set_rectangular_boundary.assert_called_once()

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
        self.boundary.set_rectangular_boundary.assert_called_once_with(
            "map", 0, 10, 0, 10
        )

    def test_change_map_order_of_operations(self):
        map_name = "test_map"
        map_data = MagicMock()
        self.map_loader.load_map_data.return_value = map_data

        call_order = []

        self.npc_manager.clear_npcs.side_effect = lambda: call_order.append(
            "clear_npcs"
        )
        self.map_loader.load_map_data.side_effect = (
            lambda name: call_order.append("load_map") or map_data
        )

        self.map_transition.change_map(map_name)

        self.assertEqual(call_order, ["clear_npcs", "load_map"])

    def test_update_boundaries_correct_values(self):
        self.map_manager.map_size = (20, 15)
        self.map_transition._update_boundaries()
        self.boundary.set_rectangular_boundary.assert_called_once_with(
            "map", 0, 20, 0, 15
        )

    def test_change_map_loader_failure(self):
        self.map_loader.load_map_data.side_effect = Exception(
            "Map load failed"
        )
        with self.assertRaises(Exception) as context:
            self.map_transition.change_map("broken_map")
        self.assertIn("Map load failed", str(context.exception))

    def test_reset_events_with_empty_map(self):
        map_data = MagicMock()
        self.map_transition._reset_events(map_data)
        self.event_engine.reset.assert_called_once()
        self.event_engine.set_current_map.assert_called_once_with(map_data)

    def test_change_map_twice(self):
        map_data = MagicMock()
        self.map_loader.load_map_data.return_value = map_data

        self.map_transition.change_map("map_a")
        self.map_transition.change_map("map_a")

        self.assertEqual(self.map_manager.load_map.call_count, 2)

    def test_npc_collision_removed_from_old_map(self):
        mock_npc = MagicMock()
        mock_npc.slug = "npc_test"
        mock_npc.remove_collision = MagicMock()

        old_map = MagicMock()
        self.map_manager.map_size = (10, 10)
        self.map_loader.load_map_data.return_value = old_map

        self.npc_manager.get_all_entities.return_value = [mock_npc]

        def clear_npcs_side_effect():
            for npc in self.npc_manager.get_all_entities():
                npc.remove_collision()

        self.npc_manager.clear_npcs.side_effect = clear_npcs_side_effect

        self.map_transition.change_map("new_map")

        mock_npc.remove_collision.assert_called_once()
