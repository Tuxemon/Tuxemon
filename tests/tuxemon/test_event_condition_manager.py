# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import MagicMock, patch

from tuxemon.event.eventcondition import ConditionManager


class TestConditionManager(unittest.TestCase):
    def setUp(self):
        self.condition_manager = ConditionManager()

    @patch("tuxemon.plugin.load_plugins")
    def test_get_condition(self, mock_load_plugins):
        result = self.condition_manager.get_condition("char_at")
        self.assertIsNotNone(result)
        result = self.condition_manager.get_condition("some_condition")
        self.assertIsNone(result)

    @patch("tuxemon.plugin.load_plugins")
    def test_get_conditions(self, mock_load_plugins):
        mock_conditions = {f"condition{i}": MagicMock() for i in range(10)}
        mock_load_plugins.return_value = mock_conditions
        conditions = self.condition_manager.get_conditions()
        self.assertGreater(len(conditions), 0)
