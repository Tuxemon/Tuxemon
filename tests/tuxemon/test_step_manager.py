# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import MagicMock

from tuxemon.entity_dir.steps import StepManager


class DummySession:
    def __init__(self, event_bus):
        self.client = MagicMock()
        self.client.event_bus = event_bus


class StepManagerTest(unittest.TestCase):
    def setUp(self):
        self.mock_event_bus = MagicMock()
        self.session = DummySession(self.mock_event_bus)
        self.step_tracker_manager = MagicMock()
        self.manager = StepManager(self.session, self.step_tracker_manager)

    def test_handle_steps_zero(self):
        self.manager.handle_steps(
            diff_x=1, diff_y=1, steps_moved=0, monsters_in_party=[]
        )
        self.mock_event_bus.publish.assert_not_called()

    def test_handle_steps_publish(self):
        monsters = ["monster1", "monster2"]
        self.manager.handle_steps(
            diff_x=2, diff_y=3, steps_moved=5, monsters_in_party=monsters
        )
        self.mock_event_bus.publish.assert_called_once()
        args, kwargs = self.mock_event_bus.publish.call_args
        self.assertEqual(args[0], "player_steps_moved")
        self.assertEqual(kwargs["diff_x"], 2)
        self.assertEqual(kwargs["diff_y"], 3)
        self.assertEqual(kwargs["steps"], 5)
        self.assertEqual(kwargs["monsters"], monsters)
        self.assertEqual(kwargs["session"], self.session)
