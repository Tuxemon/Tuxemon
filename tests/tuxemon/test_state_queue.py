# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import time
import unittest
from unittest.mock import MagicMock

from tuxemon.state.queue import QueuedState, StateQueue


class TestStateQueue(unittest.TestCase):

    def setUp(self):
        self.state_manager_ref = MagicMock()
        self.state_queue_manager = StateQueue(self.state_manager_ref)

    def test_init(self):
        self.assertEqual(
            self.state_queue_manager._state_manager_ref, self.state_manager_ref
        )
        self.assertEqual(self.state_queue_manager._state_queue, [])

    def test_queue_state(self):
        state_name = "test_state"
        kwargs = {"arg1": "value1", "arg2": "value2"}
        self.state_queue_manager.queue_state(state_name, priority=5, **kwargs)
        expected = QueuedState(5, state_name, kwargs)
        self.assertEqual(self.state_queue_manager._state_queue, [expected])

    def test_handle_next_state(self):
        state_name = "test_state"
        kwargs = {"arg1": "value1", "arg2": "value2"}
        self.state_queue_manager.queue_state(state_name, priority=1, **kwargs)
        self.state_queue_manager.handle_next_queued_state()
        self.state_manager_ref.replace_state.assert_called_once_with(
            state_name, **kwargs
        )

    def test_handle_next_queued_state_no_states(self):
        self.assertFalse(self.state_queue_manager.handle_next_queued_state())

    def test_get_queued_state_by_name(self):
        state_name = "test_state"
        kwargs = {"arg1": "value1", "arg2": "value2"}
        self.state_queue_manager.queue_state(state_name, priority=10, **kwargs)
        queued_state = self.state_queue_manager.get_queued_state_by_name(
            state_name
        )
        expected = QueuedState(10, state_name, kwargs)
        self.assertEqual(queued_state, expected)

    def test_get_queued_state_by_name_not_found(self):
        with self.assertRaises(ValueError):
            self.state_queue_manager.get_queued_state_by_name("missing_state")

    def test_has_queued_states(self):
        self.assertFalse(self.state_queue_manager.has_queued_states)
        self.state_queue_manager.queue_state("test_state")
        self.assertTrue(self.state_queue_manager.has_queued_states)

    def test_queued_states(self):
        state_name = "test_state"
        kwargs = {"arg1": "value1", "arg2": "value2"}
        self.state_queue_manager.queue_state(state_name, **kwargs)
        expected = [QueuedState(10, state_name, kwargs)]
        self.assertEqual(self.state_queue_manager.queued_states, expected)

    def test_multiple_queued_states_order(self):
        self.state_queue_manager.queue_state("low", priority=10)
        self.state_queue_manager.queue_state("high", priority=1)
        self.state_queue_manager.queue_state("medium", priority=5)

        expected_order = ["high", "medium", "low"]
        for name in expected_order:
            self.state_queue_manager.handle_next_queued_state()
            self.state_manager_ref.replace_state.assert_called_with(name)

    def test_queued_states_immutability(self):
        self.state_queue_manager.queue_state("test_state", arg="value")
        external_view = self.state_queue_manager.queued_states
        external_view.append(QueuedState(0, "malicious_state", {}))
        self.assertEqual(len(self.state_queue_manager.queued_states), 1)

    def test_queue_state_no_kwargs(self):
        state_name = "simple_state"
        self.state_queue_manager.queue_state(state_name, priority=3)
        expected = QueuedState(3, state_name, {})
        self.assertEqual(self.state_queue_manager._state_queue, [expected])

    def test_clear(self):
        self.state_queue_manager.queue_state("state1")
        self.state_queue_manager.queue_state("state2")
        self.state_queue_manager.clear()
        self.assertEqual(self.state_queue_manager.queued_states, [])

    def test_remove_state_by_name(self):
        self.state_queue_manager.queue_state("state1")
        self.state_queue_manager.queue_state("state2")
        self.state_queue_manager.remove_state_by_name("state1")
        expected = [QueuedState(10, "state2", {})]
        self.assertEqual(self.state_queue_manager.queued_states, expected)

    def test_remove_state_by_name_not_found(self):
        self.state_queue_manager.queue_state("state1")
        with self.assertRaises(ValueError):
            self.state_queue_manager.remove_state_by_name("missing_state")

    def test_replace_queued_state(self):
        self.state_queue_manager.queue_state("state1", arg="old")
        self.state_queue_manager.replace_queued_state(
            "state1", new_kwargs={"arg": "new"}
        )
        state = self.state_queue_manager.get_queued_state_by_name("state1")
        self.assertEqual(state.kwargs["arg"], "new")

    def test_replace_queued_state_not_found(self):
        with self.assertRaises(ValueError):
            self.state_queue_manager.replace_queued_state(
                "missing_state", new_kwargs={"arg": "x"}
            )

    def test_peek_next(self):
        self.state_queue_manager.queue_state("state1", arg="peek")
        next_state = self.state_queue_manager.peek_next()
        expected = QueuedState(10, "state1", {"arg": "peek"})
        self.assertEqual(next_state, expected)

    def test_peek_next_empty(self):
        self.assertIsNone(self.state_queue_manager.peek_next())

    def test_state_not_activated_before_activation_time(self):
        future_time = time.time() + 5  # 5 seconds in the future
        self.state_queue_manager.queue_state(
            "future_state", activation_time=future_time
        )
        activated = self.state_queue_manager.handle_next_queued_state()
        self.assertFalse(activated)
        self.assertTrue(self.state_queue_manager.has_queued_states)

    def test_state_skipped_after_expiration(self):
        past_time = time.time() - 5  # Already expired
        self.state_queue_manager.queue_state(
            "expired_state", expires_at=past_time
        )
        activated = self.state_queue_manager.handle_next_queued_state()
        self.assertFalse(activated)
        self.assertTrue(self.state_queue_manager.has_queued_states)

    def test_remove_expired_states(self):
        # One expired, one valid
        expired_time = time.time() - 10
        valid_time = time.time() + 10

        self.state_queue_manager.queue_state(
            "expired_state", expires_at=expired_time
        )
        self.state_queue_manager.queue_state(
            "valid_state", expires_at=valid_time
        )

        self.state_queue_manager.remove_expired_states()

        queued_names = [
            state.name for state in self.state_queue_manager.queued_states
        ]
        self.assertEqual(queued_names, ["valid_state"])

    def test_state_activation_and_expiration_window(self):
        now = time.time()
        activation_time = now + 0.01  # activates in 10ms
        expires_at = now + 0.5  # expires in 500ms

        self.state_queue_manager.queue_state(
            "timed_state",
            activation_time=activation_time,
            expires_at=expires_at,
        )

        activated = self.state_queue_manager.handle_next_queued_state()
        self.assertFalse(activated)

        time.sleep(0.02)
        activated = self.state_queue_manager.handle_next_queued_state()
        self.assertTrue(activated)
        self.state_manager_ref.replace_state.assert_called_once_with(
            "timed_state"
        )

    def test_get_queued_states_by_source(self):
        self.state_queue_manager.queue_state("cutscene_1", source="cutscene")
        self.state_queue_manager.queue_state("quest_1", source="quest")
        self.state_queue_manager.queue_state("cutscene_2", source="cutscene")

        cutscene_states = [
            state
            for state in self.state_queue_manager.queued_states
            if state.source == "cutscene"
        ]

        self.assertEqual(len(cutscene_states), 2)
        self.assertTrue(
            all(state.source == "cutscene" for state in cutscene_states)
        )

    def test_state_skipped_due_to_unmet_condition(self):
        condition = lambda: False
        self.state_queue_manager.queue_state(
            "locked_state", condition=condition
        )
        activated = self.state_queue_manager.handle_next_queued_state()
        self.assertFalse(activated)
        self.assertTrue(self.state_queue_manager.has_queued_states)
