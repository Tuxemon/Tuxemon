# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import MagicMock, patch

from tuxemon.client import LocalPygameClient
from tuxemon.config import TuxemonConfig
from tuxemon.main import (
    configure_debug_options,
    configure_game_states,
)


class TestGameInitialization(unittest.TestCase):
    def setUp(self):
        self.mock_config = MagicMock(spec=TuxemonConfig)
        self.mock_screen = MagicMock()
        self.mock_client = MagicMock(spec=LocalPygameClient)
        self.mock_client.state_manager = MagicMock()
        self.mock_client.event_engine = MagicMock()

    @patch("tuxemon.client.LocalPygameClient.create")
    def test_create_client_success(self, MockCreate):
        MockCreate.return_value = self.mock_client

        client = LocalPygameClient.create(self.mock_config, self.mock_screen)

        self.assertEqual(client, self.mock_client)
        MockCreate.assert_called_once_with(self.mock_config, self.mock_screen)

    @patch("tuxemon.client.LocalPygameClient.create")
    def test_create_client_failure(self, MockCreate):
        MockCreate.side_effect = TypeError("Invalid arguments")

        with self.assertRaises(TypeError):
            LocalPygameClient.create(self.mock_config, self.mock_screen)

    def test_configure_game_states_with_load_slot(self):
        load_slot = 1
        self.mock_config.mods = ["mod1"]
        self.mock_config.skip_titlescreen = False
        self.mock_config.splash = False

        configure_game_states(self.mock_client, self.mock_config, load_slot)

        self.mock_client.push_state.assert_any_call("BackgroundState")
        self.mock_client.push_state.assert_any_call("StartState")
        self.mock_client.push_state.assert_any_call(
            "LoadMenuState", load_slot=load_slot
        )
        self.mock_client.pop_state.assert_called_once()

    def test_configure_game_states_without_load_slot(self):
        load_slot = None
        self.mock_config.mods = ["mod1"]
        self.mock_config.skip_titlescreen = False
        self.mock_config.splash = True

        configure_game_states(self.mock_client, self.mock_config, load_slot)

        self.mock_client.push_state.assert_any_call("BackgroundState")
        self.mock_client.push_state.assert_any_call("StartState")
        self.mock_client.push_state.assert_any_call(
            "SplashState", parent=self.mock_client.state_manager
        )
        self.mock_client.push_state.assert_any_call("FadeInTransition")

    def test_configure_debug_options(self):
        configure_debug_options(self.mock_client)

        action = self.mock_client.event_engine.execute_action
        action.assert_any_call("add_monster", ("bigfin", 10))
        action.assert_any_call("add_monster", ("dandylion", 10))
        action.assert_any_call("add_item", ("potion",))
        action.assert_any_call("add_item", ("cherry",))
        action.assert_any_call("add_item", ("tuxeball",))
        action.assert_any_call("add_item", ("super_potion",))
        action.assert_any_call("add_item", ("apple",))
