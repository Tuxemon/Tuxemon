# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import MagicMock

from tuxemon.camera.camera import CameraManager
from tuxemon.client import LocalPygameClient
from tuxemon.db import Direction
from tuxemon.event.eventmanager import EventManager
from tuxemon.movement import MovementManager
from tuxemon.npc import NPC
from tuxemon.platform.const import intentions
from tuxemon.platform.input_manager import InputManager


class TestMovementManager(unittest.TestCase):

    def setUp(self):
        self.mock_client = MagicMock(spec=LocalPygameClient)
        self.mock_client.event_manager = MagicMock(spec=EventManager)
        self.mock_client.input_manager = MagicMock(spec=InputManager)
        self.mock_client.camera_manager = MagicMock(spec=CameraManager)
        self.movement_manager = MovementManager(
            self.mock_client.event_manager,
            self.mock_client.input_manager,
            self.mock_client.camera_manager,
        )
        self.mock_npc = MagicMock(spec=NPC)
        self.mock_npc.slug = "npc_1"
        self.mock_npc.mover = MagicMock()

    def test_move_char(self):
        self.movement_manager.move_char(self.mock_npc, Direction.up)
        self.mock_npc.set_move_direction.assert_called_with(Direction.up)

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
        self.mock_npc.set_move_direction.assert_called_with(Direction.down)

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

    def test_handle_directional_input_valid_and_allowed(self):
        mock_camera = MagicMock()
        mock_camera.is_following.return_value = True
        self.mock_client.camera_manager.get_active_camera.return_value = (
            mock_camera
        )
        self.movement_manager.allow_char_movement.add("npc_1")

        event = MagicMock()
        event.button = next(iter(self.movement_manager.direction_map))
        event.held = True
        event.pressed = True

        result = self.movement_manager.handle_directional_input(
            self.mock_npc, event
        )
        self.assertIsNone(result)
        self.mock_npc.set_move_direction.assert_called_once()

    def test_handle_directional_input_valid_but_not_allowed(self):
        mock_camera = MagicMock()
        mock_camera.is_following.return_value = True
        self.mock_client.camera_manager.get_active_camera.return_value = (
            mock_camera
        )

        event = MagicMock()
        event.button = next(iter(self.movement_manager.direction_map))
        event.held = True
        event.pressed = True

        result = self.movement_manager.handle_directional_input(
            self.mock_npc, event
        )
        self.assertIsNone(result)
        self.mock_npc.set_move_direction.assert_not_called()

    def test_handle_directional_input_camera_not_following(self):
        mock_camera = MagicMock()
        mock_camera.is_following.return_value = False
        self.mock_client.camera_manager.get_active_camera.return_value = (
            mock_camera
        )

        event = MagicMock()
        event.button = next(iter(self.movement_manager.direction_map))
        event.held = True
        event.pressed = True

        self.movement_manager.handle_directional_input(self.mock_npc, event)
        self.mock_client.camera_manager.handle_input.assert_called_with(event)

    def test_handle_directional_input_release(self):
        mock_camera = MagicMock()
        mock_camera.is_following.return_value = True
        self.mock_client.camera_manager.get_active_camera.return_value = (
            mock_camera
        )

        self.movement_manager.wants_to_move_char["npc_1"] = Direction.down

        event = MagicMock()
        event.button = intentions.DOWN
        event.held = False
        event.pressed = False

        result = self.movement_manager.handle_directional_input(
            self.mock_npc, event
        )
        self.assertIsNone(result)
        self.mock_npc.cancel_movement.assert_called_once()

    def test_handle_directional_input_invalid_button(self):
        event = MagicMock()
        event.button = 9999
        event.held = True
        event.pressed = True

        result = self.movement_manager.handle_directional_input(
            self.mock_npc, event
        )
        self.assertEqual(result, event)
