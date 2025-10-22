# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import MagicMock

from tuxemon import prepare
from tuxemon.platform.const import intentions
from tuxemon.world.input import InputHandlerConfig, WorldInputHandler


class TestWorldInputHandler(unittest.TestCase):
    def setUp(self):
        self.mock_player = MagicMock()
        self.mock_client = MagicMock()
        self.mock_menu_manager = MagicMock()
        self.handler = WorldInputHandler(
            self.mock_player, self.mock_client, self.mock_menu_manager
        )

        prepare.DEV_TOOLS = True

        self.event = MagicMock()
        self.event.held = True
        self.event.pressed = True
        self.event.button = intentions.RUN

    def test_handle_run(self):
        result = self.handler.handle_run(self.event)
        self.mock_player.mover.update_movement_state.assert_called_with(True)
        self.assertEqual(result, self.event)

    def test_handle_noclip_toggle(self):
        self.mock_player.ignore_collisions = False
        result = self.handler.handle_noclip(self.event)
        self.assertTrue(self.mock_player.ignore_collisions)
        self.assertIsNone(result)

    def test_handle_noclip_no_toggle_when_not_pressed(self):
        self.event.pressed = False
        self.mock_player.ignore_collisions = False
        result = self.handler.handle_noclip(self.event)
        self.assertFalse(self.mock_player.ignore_collisions)
        self.assertEqual(result, self.event)

    def test_handle_reload_map(self):
        mock_map = MagicMock()
        self.mock_client.map_manager.current_map = mock_map
        result = self.handler.handle_reload_map(self.event)
        mock_map.reload_tiles.assert_called_once()
        self.assertIsNone(result)

    def test_handle_reload_map_not_pressed(self):
        self.event.pressed = False
        result = self.handler.handle_reload_map(self.event)
        self.assertEqual(result, self.event)

    def test_handle_world_menu(self):
        result = self.handler.handle_world_menu(self.event)
        self.mock_client.event_manager.release_controls.assert_called_with(
            self.mock_client.input_manager
        )
        self.mock_client.push_state.assert_called_once()
        self.assertIsNone(result)

    def test_handle_world_menu_not_pressed(self):
        self.event.pressed = False
        result = self.handler.handle_world_menu(self.event)
        self.assertEqual(result, self.event)

    def test_handle_interact_pressed(self):
        result = self.handler.handle_interact(self.event)
        self.assertEqual(result, self.event)

    def test_handle_interact_not_pressed(self):
        self.event.pressed = False
        result = self.handler.handle_interact(self.event)
        self.assertEqual(result, self.event)

    def test_get_handlers_structure(self):
        handlers = self.handler.get_handlers()
        self.assertIsInstance(handlers, dict)
        for button, config in handlers.items():
            self.assertIsInstance(config, InputHandlerConfig)
            self.assertTrue(callable(config.handler))
            self.assertIsInstance(config.description, str)
            self.assertIn(
                button,
                [
                    intentions.RUN,
                    intentions.NOCLIP,
                    intentions.RELOAD_MAP,
                    intentions.WORLD_MENU,
                    intentions.INTERACT,
                ],
            )
