# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import Mock

from tuxemon.event.eventengine import EventState, RunningEvent


class TestRunningEvent(unittest.TestCase):
    def test_init(self):
        map_event = Mock(acts=[1, 2])
        event = RunningEvent(map_event)
        self.assertEqual(map_event, event.map_event)
        self.assertEqual({}, event.context)
        self.assertEqual(0, event.action_index)
        self.assertIsNone(event.current_action)
        self.assertEqual(EventState.WAITING, event.state)

    def test_get_next_action(self):
        map_event = Mock(acts=[1, 2])
        event = RunningEvent(map_event)
        self.assertEqual(1, event.get_next_action())
        event.advance()
        self.assertEqual(2, event.get_next_action())
        event.advance()
        self.assertIsNone(event.get_next_action())

    def test_advance(self):
        map_event = Mock(acts=[1, 2])
        event = RunningEvent(map_event)
        event.advance()
        self.assertEqual(1, event.action_index)
        event.advance()
        self.assertEqual(2, event.action_index)

    def test_cancel(self):
        map_event = Mock(acts=[1, 2])
        event = RunningEvent(map_event)
        event.cancel()
        self.assertEqual(EventState.CANCELLED, event.state)
        self.assertTrue(event.is_cancelled())

    def test_context(self):
        map_event = Mock(acts=[1, 2])
        event = RunningEvent(map_event)
        event.context["a"] = 1
        self.assertEqual({"a": 1}, event.context)

    def test_state_transitions(self):
        map_event = Mock(acts=[1])
        event = RunningEvent(map_event)
        self.assertEqual(event.state, EventState.WAITING)

        event.running()
        self.assertEqual(event.state, EventState.RUNNING)
        self.assertTrue(event.is_running())

        event.cancel()
        self.assertEqual(event.state, EventState.CANCELLED)
        self.assertTrue(event.is_cancelled())

    def test_get_next_action_exhausted(self):
        map_event = Mock(acts=[1])
        event = RunningEvent(map_event)
        event.advance()
        self.assertIsNone(event.get_next_action())

    def test_cancel_all_events(self):
        map_event = Mock(acts=[1])
        event1 = RunningEvent(map_event)
        event2 = RunningEvent(map_event)
        event1.running()
        event2.running()

        manager = Mock()
        manager.running_events = {1: event1, 2: event2}
        manager.cancel_all_events = lambda: [
            e.cancel() for e in manager.running_events.values()
        ]

        manager.cancel_all_events()
        self.assertEqual(event1.state, EventState.CANCELLED)
        self.assertEqual(event2.state, EventState.CANCELLED)

    def test_context_persistence(self):
        map_event = Mock(acts=[1])
        event = RunningEvent(map_event)
        event.context["score"] = 42
        event.context["score"] += 8
        self.assertEqual(event.context["score"], 50)

    def test_tick_accumulates_elapsed_time(self):
        map_event = Mock(acts=[1], timeout=None, delay=None)
        event = RunningEvent(map_event)

        self.assertEqual(event.elapsed_time, 0.0)
        ready = event.tick(1.5)
        self.assertTrue(ready)
        self.assertAlmostEqual(event.elapsed_time, 1.5)

        ready = event.tick(2.0)
        self.assertTrue(ready)
        self.assertAlmostEqual(event.elapsed_time, 3.5)

    def test_tick_respects_delay(self):
        map_event = Mock(acts=[1], timeout=None, delay=3.0)
        event = RunningEvent(map_event)

        self.assertFalse(event.tick(2.0))
        self.assertEqual(event.elapsed_time, 2.0)

        self.assertTrue(event.tick(2.0))
        self.assertEqual(event.elapsed_time, 4.0)

    def test_tick_respects_timeout(self):
        map_event = Mock(acts=[1], timeout=5.0, delay=None)
        event = RunningEvent(map_event)

        self.assertTrue(event.tick(4.0))
        self.assertFalse(event.is_cancelled())
        self.assertEqual(event.elapsed_time, 4.0)

        self.assertFalse(event.tick(2.0))
        self.assertTrue(event.is_cancelled())

    def test_tick_delay_and_timeout_combined(self):
        map_event = Mock(acts=[1], timeout=8.0, delay=3.0)
        event = RunningEvent(map_event)

        self.assertFalse(event.tick(2.0))
        self.assertEqual(event.elapsed_time, 2.0)

        self.assertTrue(event.tick(2.0))
        self.assertFalse(event.is_cancelled())

        self.assertFalse(event.tick(5.0))
        self.assertTrue(event.is_cancelled())

    def test_tick_active_window(self):
        map_event = Mock(acts=[1], delay=3.0, timeout=8.0)
        event = RunningEvent(map_event)

        self.assertFalse(event.tick(2.0))
        self.assertFalse(event.is_cancelled())

        self.assertTrue(event.tick(2.0))
        self.assertFalse(event.is_cancelled())

        self.assertTrue(event.tick(3.0))
        self.assertFalse(event.is_cancelled())

        self.assertFalse(event.tick(2.0))
        self.assertTrue(event.is_cancelled())

    def test_tick_active_window_with_context_flag(self):
        map_event = Mock(acts=[1], delay=3.0, timeout=8.0)
        event = RunningEvent(map_event)

        self.assertFalse(event.tick(2.0))
        self.assertFalse(event.is_cancelled())
        self.assertNotIn("window_triggered", event.context)

        ready = event.tick(2.0)
        self.assertTrue(ready)
        if ready and not event.context.get("window_triggered"):
            event.context["window_triggered"] = True
        self.assertTrue(event.context["window_triggered"])

        ready = event.tick(2.0)
        self.assertTrue(ready)
        self.assertTrue(event.context["window_triggered"])

        ready = event.tick(3.0)
        self.assertFalse(ready)
        self.assertTrue(event.is_cancelled())
