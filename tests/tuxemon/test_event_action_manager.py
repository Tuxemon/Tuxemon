# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import MagicMock, patch

from tuxemon.event.eventaction import ActionManager


class TestActionManager(unittest.TestCase):
    def setUp(self):
        self.action_manager = ActionManager()

    @patch("tuxemon.plugin.load_plugins")
    def test_init(self, mock_load_plugins):
        mock_load_plugins.return_value = {}
        self.assertGreater(len(self.action_manager.actions), 0)

    @patch("tuxemon.plugin.load_plugins")
    def test_get_action(self, mock_load_plugins):
        mock_action = MagicMock(return_value="add_monster")
        mock_load_plugins.return_value = {"add_monster": mock_action}
        result = self.action_manager.get_action(
            "add_monster", ["monster_slug", 1]
        )
        self.assertIsNotNone(result)

    @patch("tuxemon.plugin.load_plugins")
    def test_get_action_not_implemented(self, mock_load_plugins):
        mock_load_plugins.return_value = {}
        result = self.action_manager.get_action("action2")
        self.assertIsNone(result)

    @patch("tuxemon.plugin.load_plugins")
    def test_get_action_with_type_error(self, mock_load_plugins):
        mock_action = MagicMock(side_effect=TypeError("Test error"))
        mock_load_plugins.return_value = {"add_monster": mock_action}
        result = self.action_manager.get_action(
            "add_monster", ["param1", "param2"]
        )
        self.assertIsNone(result)

    @patch("tuxemon.plugin.load_plugins")
    def test_get_actions(self, mock_load_plugins):
        mock_load_plugins.return_value = {}
        actions = self.action_manager.get_actions()
        self.assertGreater(len(actions), 0)
