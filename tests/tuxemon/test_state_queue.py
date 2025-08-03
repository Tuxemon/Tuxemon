# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import MagicMock

from tuxemon.state.queue import StateQueue


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
        self.state_queue_manager.queue_state(state_name, **kwargs)
        self.assertEqual(
            self.state_queue_manager._state_queue, [(state_name, kwargs)]
        )

    def test_handle_next_queued_state(self):
        state_name = "test_state"
        kwargs = {"arg1": "value1", "arg2": "value2"}
        self.state_queue_manager.queue_state(state_name, **kwargs)
        self.state_queue_manager.handle_next_queued_state()
        self.state_manager_ref.replace_state.assert_called_once_with(
            state_name, **kwargs
        )

    def test_handle_next_queued_state_no_states(self):
        self.assertFalse(self.state_queue_manager.handle_next_queued_state())

    def test_get_queued_state_by_name(self):
        state_name = "test_state"
        kwargs = {"arg1": "value1", "arg2": "value2"}
        self.state_queue_manager.queue_state(state_name, **kwargs)
        queued_state = self.state_queue_manager.get_queued_state_by_name(
            state_name
        )
        self.assertEqual(queued_state, (state_name, kwargs))

    def test_get_queued_state_by_name_not_found(self):
        state_name = "test_state"
        with self.assertRaises(ValueError):
            self.state_queue_manager.get_queued_state_by_name(state_name)

    def test_has_queued_states(self):
        self.assertFalse(self.state_queue_manager.has_queued_states)
        self.state_queue_manager.queue_state("test_state")
        self.assertTrue(self.state_queue_manager.has_queued_states)

    def test_queued_states(self):
        state_name = "test_state"
        kwargs = {"arg1": "value1", "arg2": "value2"}
        self.state_queue_manager.queue_state(state_name, **kwargs)
        queued_states = self.state_queue_manager.queued_states
        self.assertEqual(queued_states, [(state_name, kwargs)])

    def test_multiple_queued_states_order(self):
        states = [
            ("state_one", {"x": 1}),
            ("state_two", {"y": 2}),
            ("state_three", {"z": 3}),
        ]
        for name, kwargs in states:
            self.state_queue_manager.queue_state(name, **kwargs)

        for name, kwargs in states:
            self.state_queue_manager.handle_next_queued_state()
            self.state_manager_ref.replace_state.assert_called_with(
                name, **kwargs
            )

    def test_queued_states_immutability(self):
        self.state_queue_manager.queue_state("test_state", arg="value")
        external_view = self.state_queue_manager.queued_states
        external_view.append(("malicious_state", {}))
        self.assertEqual(len(self.state_queue_manager.queued_states), 1)

    def test_queue_state_no_kwargs(self):
        state_name = "simple_state"
        self.state_queue_manager.queue_state(state_name)
        self.assertEqual(
            self.state_queue_manager._state_queue, [(state_name, {})]
        )

    def test_clear(self):
        self.state_queue_manager.queue_state("state1")
        self.state_queue_manager.queue_state("state2")
        self.state_queue_manager.clear()
        self.assertEqual(self.state_queue_manager.queued_states, [])

    def test_remove_state_by_name(self):
        self.state_queue_manager.queue_state("state1")
        self.state_queue_manager.queue_state("state2")
        self.state_queue_manager.remove_state_by_name("state1")
        self.assertEqual(
            self.state_queue_manager.queued_states, [("state2", {})]
        )

    def test_remove_state_by_name_not_found(self):
        self.state_queue_manager.queue_state("state1")
        with self.assertRaises(ValueError):
            self.state_queue_manager.remove_state_by_name("missing_state")

    def test_replace_queued_state(self):
        self.state_queue_manager.queue_state("state1", arg="old")
        self.state_queue_manager.replace_queued_state("state1", arg="new")
        state = self.state_queue_manager.get_queued_state_by_name("state1")
        self.assertEqual(state[1]["arg"], "new")

    def test_replace_queued_state_not_found(self):
        with self.assertRaises(ValueError):
            self.state_queue_manager.replace_queued_state(
                "missing_state", arg="x"
            )

    def test_peek_next(self):
        self.state_queue_manager.queue_state("state1", arg="peek")
        next_state = self.state_queue_manager.peek_next()
        self.assertEqual(next_state, ("state1", {"arg": "peek"}))

    def test_peek_next_empty(self):
        self.assertIsNone(self.state_queue_manager.peek_next())
