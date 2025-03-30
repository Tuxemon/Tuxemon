# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import Mock

from tuxemon.event.eventengine import EventEngine, RunningEvent


class TestRunningEvent(unittest.TestCase):
    def test_advance_and_get_next_action(self):
        map_event = Mock(acts=[1, 2])
        event = RunningEvent(map_event)
        self.assertEqual(1, event.get_next_action())
        event.advance()
        self.assertEqual(2, event.get_next_action())
        event.advance()
        self.assertIsNone(event.get_next_action())


class TestEventEngine(unittest.TestCase):
    def test_(self):
        eng = EventEngine(None)
