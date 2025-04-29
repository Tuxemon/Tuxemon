# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import MagicMock

from tuxemon.event.eventaction import ActionContextManager


class TestActionContextManager(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_action = MagicMock()
        self.mock_action.cancelled = False

    def test_context_manager_enter(self):
        with ActionContextManager(self.mock_action):
            self.mock_action.start.assert_called_once()

    def test_context_manager_exit(self):
        with ActionContextManager(self.mock_action):
            pass  # Enter and exit
        self.mock_action.cleanup.assert_called_once()

    def test_cancelled_action(self):
        self.mock_action.cancelled = True
        with ActionContextManager(self.mock_action):
            self.mock_action.start.assert_not_called()
        self.mock_action.cleanup.assert_not_called()

    def test_exception_handling(self):
        self.mock_action.cleanup = MagicMock(
            side_effect=Exception("Cleanup error")
        )
        with self.assertRaises(Exception):
            with ActionContextManager(self.mock_action):
                pass
