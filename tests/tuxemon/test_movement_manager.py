# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import MagicMock

from tuxemon.client import LocalPygameClient
from tuxemon.db import Direction
from tuxemon.event.eventmanager import EventManager
from tuxemon.movement import MovementManager
from tuxemon.npc import NPC
from tuxemon.platform.input_manager import InputManager


class TestMovementManager(unittest.TestCase):

    def setUp(self):
        self.mock_client = MagicMock(spec=LocalPygameClient)
        self.mock_client.event_manager = MagicMock(spec=EventManager)
        self.mock_client.input_manager = MagicMock(spec=InputManager)
        self.movement_manager = MovementManager(self.mock_client)
        self.mock_npc = MagicMock(spec=NPC)
        self.mock_npc.slug = "npc_1"

    def test_move_char(self):
        self.movement_manager.move_char(self.mock_npc, Direction.up)
        self.assertEqual(self.mock_npc.move_direction, Direction.up)

    def test_stop_char(self):
        self.movement_manager.wants_to_move_char["npc_1"] = Direction.up
        self.movement_manager.stop_char(self.mock_npc)
        self.assertNotIn("npc_1", self.movement_manager.wants_to_move_char)
        self.mock_client.event_manager.release_controls.assert_called_once()
        self.mock_npc.cancel_movement.assert_called_once()

    def test_unlock_controls(self):
        self.movement_manager.wants_to_move_char["npc_1"] = Direction.down
        self.movement_manager.unlock_controls(self.mock_npc)
        self.assertIn("npc_1", self.movement_manager.allow_char_movement)
        self.assertEqual(self.mock_npc.move_direction, Direction.down)

    def test_lock_controls(self):
        self.movement_manager.allow_char_movement.add("npc_1")
        self.movement_manager.lock_controls(self.mock_npc)
        self.assertNotIn("npc_1", self.movement_manager.allow_char_movement)

    def test_stop_and_reset_char(self):
        self.movement_manager.wants_to_move_char["npc_1"] = Direction.left
        self.movement_manager.stop_and_reset_char(self.mock_npc)
        self.assertNotIn("npc_1", self.movement_manager.wants_to_move_char)
        self.mock_client.event_manager.release_controls.assert_called_once()
        self.mock_npc.abort_movement.assert_called_once()

    def test_is_movement_allowed(self):
        self.movement_manager.allow_char_movement.add("npc_1")
        result = self.movement_manager.is_movement_allowed(self.mock_npc)
        self.assertTrue(result)
        self.movement_manager.allow_char_movement.remove("npc_1")
        result = self.movement_manager.is_movement_allowed(self.mock_npc)
        self.assertFalse(result)

    def test_has_pending_movement(self):
        self.assertFalse(
            self.movement_manager.has_pending_movement(self.mock_npc)
        )

        self.movement_manager.wants_to_move_char["npc_1"] = Direction.up
        self.assertTrue(
            self.movement_manager.has_pending_movement(self.mock_npc)
        )

        del self.movement_manager.wants_to_move_char["npc_1"]
        self.assertFalse(
            self.movement_manager.has_pending_movement(self.mock_npc)
        )
