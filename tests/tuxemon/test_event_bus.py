# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import MagicMock

from tuxemon.event.eventbus import EventBus, Listener
from tuxemon.state.manager import StateManager
from tuxemon.state.repository import StateRepository


class TestEventBus(unittest.TestCase):
    def setUp(self):
        self.event_bus = EventBus()
        self.mock_callback = MagicMock()
        self.mock_callback1 = MagicMock()
        self.mock_callback2 = MagicMock()

    def test_register_event(self):
        self.event_bus.subscribe("test_event", self.mock_callback, priority=10)
        self.assertIn("test_event", self.event_bus._listeners)
        self.assertEqual(
            self.event_bus._listeners["test_event"],
            [Listener(10, self.mock_callback)],
        )

    def test_unregister_event(self):
        self.event_bus.subscribe("test_event", self.mock_callback, priority=10)
        self.event_bus.unsubscribe("test_event", self.mock_callback)
        self.assertNotIn("test_event", self.event_bus._listeners)

    def test_unregister_event_with_priority(self):
        self.event_bus.subscribe("test_event", self.mock_callback, priority=10)
        self.event_bus.subscribe("test_event", self.mock_callback, priority=5)
        self.event_bus.unsubscribe(
            "test_event", self.mock_callback, priority=10
        )
        self.assertIn("test_event", self.event_bus._listeners)
        self.assertEqual(
            self.event_bus._listeners["test_event"],
            [Listener(5, self.mock_callback)],
        )

    def test_trigger_event(self):
        self.event_bus.subscribe("test_event", self.mock_callback, priority=10)
        self.event_bus.publish("test_event", "arg1", kwarg1="value1")
        self.mock_callback.assert_called_once_with("arg1", kwarg1="value1")

    def test_reset_events(self):
        self.event_bus.subscribe("test_event", self.mock_callback, priority=10)
        self.assertTrue(self.event_bus._listeners)
        self.event_bus.reset_all_events()
        self.assertFalse(self.event_bus._listeners)

    def test_unregister_nonexistent_event(self):
        with self.assertRaises(ValueError):
            self.event_bus.unsubscribe("nonexistent_event", self.mock_callback)

    def test_multiple_callbacks_priority_order(self):
        calls = []

        def cb1(*args, **kwargs):
            calls.append("cb1")

        def cb2(*args, **kwargs):
            calls.append("cb2")

        self.event_bus.subscribe("test_event", cb1, priority=5)
        self.event_bus.subscribe("test_event", cb2, priority=10)

        self.event_bus.publish("test_event")
        self.assertEqual(calls, ["cb2", "cb1"])

    def test_publish_no_listeners(self):
        try:
            self.event_bus.publish("no_listeners_event")
        except Exception as e:
            self.fail(f"Publish raised an exception unexpectedly: {e}")

    def test_duplicate_callback_registration(self):
        self.event_bus.subscribe("test_event", self.mock_callback, priority=10)
        self.event_bus.subscribe("test_event", self.mock_callback, priority=5)

        listeners = self.event_bus._listeners["test_event"]
        self.assertEqual(len(listeners), 2)
        self.assertIn(Listener(10, self.mock_callback), listeners)
        self.assertIn(Listener(5, self.mock_callback), listeners)

    def test_listener_sorting_stability_same_priority(self):
        calls = []

        def cb1(*args, **kwargs):
            calls.append("cb1")

        def cb2(*args, **kwargs):
            calls.append("cb2")

        self.event_bus.subscribe("test_event", cb1, priority=5)
        self.event_bus.subscribe("test_event", cb2, priority=5)

        self.event_bus.publish("test_event")
        self.assertEqual(calls, ["cb1", "cb2"])

    def test_callback_exception_handling(self):
        def faulty_callback(*args, **kwargs):
            raise RuntimeError("Intentional error")

        safe_callback = MagicMock()

        self.event_bus.subscribe("test_event", faulty_callback, priority=10)
        self.event_bus.subscribe("test_event", safe_callback, priority=5)

        self.event_bus.publish("test_event", "arg")
        safe_callback.assert_called_once_with("arg")

    def test_listener_identity_distinction(self):
        def cb1(*args, **kwargs):
            pass

        def cb2(*args, **kwargs):
            pass

        self.event_bus.subscribe("test_event", cb1, priority=5)
        self.event_bus.subscribe("test_event", cb2, priority=5)

        listeners = self.event_bus._listeners["test_event"]
        self.assertEqual(len(listeners), 2)
        self.assertNotEqual(listeners[0].callback, listeners[1].callback)


class TestStateManagerEvents(unittest.TestCase):

    def setUp(self):
        self.manager = StateManager("test", EventBus(), StateRepository())
        self.mock_callback = MagicMock()
        self.mock_callback1 = MagicMock()
        self.mock_callback2 = MagicMock()

    def test_global_events(self):
        self.manager.register_global_event(
            "pre_state_update", self.mock_callback
        )
        self.manager.update(0.1)
        self.mock_callback.assert_called_once_with(0.1)
        self.mock_callback.reset_mock()

        self.manager.register_global_event(
            "post_state_update", self.mock_callback
        )
        self.manager.update(0.1)
        self.mock_callback.assert_called()
        self.mock_callback.reset_mock()

        self.manager.unregister_global_event(
            "pre_state_update", self.mock_callback
        )
        self.manager.update(0.1)
        self.mock_callback.assert_called_once_with(0.1)

    def test_global_events_multiple_callbacks(self):
        self.manager.register_global_event(
            "pre_state_update", self.mock_callback1
        )
        self.manager.register_global_event(
            "pre_state_update", self.mock_callback2
        )
        self.manager.update(0.1)

        self.mock_callback1.assert_called_once_with(0.1)
        self.mock_callback2.assert_called_once_with(0.1)

    def test_global_events_unregister_nonexistent(self):
        self.manager.event_bus.reset_all_events()
        with self.assertRaises(ValueError):
            self.manager.unregister_global_event(
                "pre_state_update", self.mock_callback
            )

    def test_reset_events(self):
        self.manager.register_global_event(
            "test_event", self.mock_callback, priority=10
        )
        self.assertTrue(self.manager.event_bus._listeners)

        self.manager.event_bus.reset_all_events()
        self.assertFalse(self.manager.event_bus._listeners)

    def test_global_events_unregister_correct_callback(self):
        self.manager.register_global_event(
            "pre_state_update", self.mock_callback1
        )
        self.manager.register_global_event(
            "pre_state_update", self.mock_callback2
        )
        self.manager.unregister_global_event(
            "pre_state_update", self.mock_callback1
        )
        self.manager.update(0.1)
        self.mock_callback1.assert_not_called()
        self.mock_callback2.assert_called_once()

    def test_state_manager_event_isolation(self):
        manager1 = StateManager("test1", EventBus(), StateRepository())
        manager2 = StateManager("test2", EventBus(), StateRepository())

        manager1.register_global_event("pre_state_update", self.mock_callback1)
        manager2.register_global_event("pre_state_update", self.mock_callback2)

        manager1.update(0.1)
        manager2.update(0.1)

        self.mock_callback1.assert_called_once_with(0.1)
        self.mock_callback2.assert_called_once_with(0.1)
