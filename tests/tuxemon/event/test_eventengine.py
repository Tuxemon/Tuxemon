import unittest
from unittest.mock import Mock

from tuxemon.event import EventEngine, RunningEvent


class TestRunningEvent(unittest.TestCase):
    def test_advance_and_get_next_action(self):
        map_event = Mock(acts=[1, 2])
        event = RunningEvent(None, map_event)
        self.assertEqual(1, event.get_next_action())
        event.advance()
        self.assertEqual(2, event.get_next_action())
        event.advance()
        self.assertIsNone(event.get_next_action())


class TestEventEngine(unittest.TestCase):
    def test_(self):
        eng = EventEngine(None)
