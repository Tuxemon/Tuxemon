# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest import skip
from unittest.mock import Mock

from tuxemon.state import State, StateManager


def create_state(name):
    mock_state = Mock(spec=State, name=f"mock {name}")
    mock_state.__name__ = name
    return mock_state


class StateManagerTestBase(unittest.TestCase):
    def create_and_register_state(self, name):
        state = create_state(name)
        self.sm.register_state(state)
        return state


class PushWhenEmpty(StateManagerTestBase):
    def setUp(self):
        self.sm = StateManager("head.tail")
        self.create_and_register_state("a")
        self.state_a = self.sm.push_state("a")
        self.sm.update(0)

    def test_current_state(self):
        self.assertEqual(self.state_a, self.sm.current_state)

    def test_pushed_in_active_states(self):
        self.assertIn(self.state_a, self.sm.active_states)

    def test_pushed_state(self):
        self.assertEqual(1, self.state_a.resume.call_count)
        self.assertEqual(0, self.state_a.pause.call_count)
        self.assertEqual(0, self.state_a.shutdown.call_count)


class PushWhenNotEmpty(StateManagerTestBase):
    def setUp(self):
        self.sm = StateManager("head.tail")
        self.create_and_register_state("a")
        self.create_and_register_state("b")
        self.state_a = self.sm.push_state("a")
        self.state_b = self.sm.push_state("b")
        self.sm.update(0)

    def test_current_state(self):
        self.assertEqual(self.state_b, self.sm.current_state)

    def test_new_in_active_states(self):
        self.assertIn(self.state_b, self.sm.active_states)

    def test_old_in_active_states(self):
        self.assertIn(self.state_a, self.sm.active_states)

    def test_new_state(self):
        self.assertEqual(1, self.state_b.resume.call_count)
        self.assertEqual(0, self.state_b.pause.call_count)
        self.assertEqual(0, self.state_b.shutdown.call_count)

    def test_old_state(self):
        self.assertEqual(1, self.state_a.resume.call_count)
        self.assertEqual(1, self.state_a.pause.call_count)
        self.assertEqual(0, self.state_a.shutdown.call_count)


class Pop(StateManagerTestBase):
    def setUp(self):
        self.sm = StateManager("head.tail")
        self.create_and_register_state("a")
        self.create_and_register_state("b")
        self.state_a = self.sm.push_state("a")
        self.state_b = self.sm.push_state("b")
        self.sm.pop_state()
        self.sm.update(0)

    def test_current_state(self):
        self.assertEqual(self.state_a, self.sm.current_state)

    def test_popped_not_in_active_states(self):
        self.assertNotIn(self.state_b, self.sm.active_states)

    def test_remaining_active_states(self):
        self.assertIn(self.state_a, self.sm.active_states)

    def test_popped_state(self):
        self.assertEqual(1, self.state_b.resume.call_count)
        self.assertEqual(1, self.state_b.pause.call_count)
        self.assertEqual(1, self.state_b.shutdown.call_count)

    def test_remaining_state(self):
        self.assertEqual(2, self.state_a.resume.call_count)
        self.assertEqual(1, self.state_a.pause.call_count)
        self.assertEqual(0, self.state_a.shutdown.call_count)

    def test_after_last_pop(self):
        self.sm.pop_state()
        self.assertIsNone(self.sm.current_state)
        self.assertEqual(2, self.state_a.resume.call_count)
        self.assertEqual(2, self.state_a.pause.call_count)
        self.assertEqual(1, self.state_a.shutdown.call_count)
        self.assertEqual(1, self.state_b.resume.call_count)
        self.assertEqual(1, self.state_b.pause.call_count)
        self.assertEqual(1, self.state_b.shutdown.call_count)


class Resume(StateManagerTestBase):
    def setUp(self):
        self.sm = StateManager("head.tail")
        self.create_and_register_state("a")
        self.create_and_register_state("b")
        self.state_a = self.sm.push_state("a")

    def test_resume_not_called_before_update(self):
        self.assertEqual(0, self.state_a.update.call_count)
        self.assertEqual(0, self.state_a.resume.call_count)
        self.assertEqual(0, self.state_a.pause.call_count)
        self.assertEqual(0, self.state_a.shutdown.call_count)

    def test_resume_called_during_update(self):
        self.sm.update(0)
        self.assertEqual(1, self.state_a.update.call_count)
        self.assertEqual(1, self.state_a.resume.call_count)
        self.assertEqual(0, self.state_a.pause.call_count)
        self.assertEqual(0, self.state_a.shutdown.call_count)

    def test_resume_called_during_update_after_pop(self):
        self.state_b = self.sm.push_state("b")
        self.sm.pop_state()
        self.sm.update(0)
        self.assertEqual(1, self.state_a.update.call_count)
        self.assertEqual(2, self.state_a.resume.call_count)
        self.assertEqual(1, self.state_a.pause.call_count)
        self.assertEqual(0, self.state_a.shutdown.call_count)


class RemoveWhenCurrent(StateManagerTestBase):
    def setUp(self):
        self.sm = StateManager("head.tail")
        self.create_and_register_state("a")
        self.create_and_register_state("b")
        self.state_a = self.sm.push_state("a")
        self.state_b = self.sm.push_state("b")
        # remove the current state
        self.sm.remove_state(self.state_b)
        self.sm.update(0)

    def test_current_state(self):
        self.assertEqual(self.state_a, self.sm.current_state)

    def test_removed_not_in_active_states(self):
        self.assertNotIn(self.state_b, self.sm.active_states)

    def test_remaining_in_active_states(self):
        self.assertIn(self.state_a, self.sm.active_states)

    def test_removed_state(self):
        self.assertEqual(1, self.state_b.resume.call_count)
        self.assertEqual(1, self.state_b.pause.call_count)
        self.assertEqual(1, self.state_b.shutdown.call_count)

    def test_remaining_state(self):
        self.assertEqual(2, self.state_a.resume.call_count)
        self.assertEqual(1, self.state_a.pause.call_count)
        self.assertEqual(0, self.state_a.shutdown.call_count)


class RemoveWhenNotCurrent(StateManagerTestBase):
    def setUp(self):
        self.sm = StateManager("head.tail")
        self.create_and_register_state("a")
        self.create_and_register_state("b")
        self.state_a = self.sm.push_state("a")
        self.state_b = self.sm.push_state("b")
        # remove a state that is not current
        self.sm.remove_state(self.state_a)
        self.sm.update(0)

    def test_current_state(self):
        self.assertEqual(self.state_b, self.sm.current_state)

    def test_removed_not_in_active_states(self):
        self.assertNotIn(self.state_a, self.sm.active_states)

    def test_remaining_in_active_states(self):
        self.assertIn(self.state_b, self.sm.active_states)

    def test_removed_state(self):
        self.assertEqual(1, self.state_a.resume.call_count)
        self.assertEqual(1, self.state_a.pause.call_count)
        self.assertEqual(1, self.state_a.shutdown.call_count)

    def test_remaining_state(self):
        self.assertEqual(1, self.state_b.resume.call_count)
        self.assertEqual(0, self.state_b.pause.call_count)
        self.assertEqual(0, self.state_b.shutdown.call_count)


class Replace(StateManagerTestBase):
    def setUp(self):
        self.sm = StateManager("head.tail")
        self.create_and_register_state("a")
        self.create_and_register_state("b")
        self.state_a = self.sm.push_state("a")
        self.state_b = self.sm.replace_state("b")
        self.sm.update(0)

    def test_current_state(self):
        self.assertEqual(self.state_b, self.sm.current_state)

    def test_new_in_active_states(self):
        self.assertIn(self.state_b, self.sm.active_states)

    def test_replaced_not_in_active_states(self):
        self.assertNotIn(self.state_a, self.sm.active_states)

    def test_new_state(self):
        self.assertEqual(1, self.state_b.resume.call_count)
        self.assertEqual(0, self.state_b.pause.call_count)
        self.assertEqual(0, self.state_b.shutdown.call_count)

    def test_replaced_state(self):
        self.assertEqual(1, self.state_a.resume.call_count)
        self.assertEqual(1, self.state_a.pause.call_count)
        self.assertEqual(1, self.state_a.shutdown.call_count)


class Enqueue(StateManagerTestBase):
    def setUp(self):
        self.sm = StateManager("head.tail")
        self.create_and_register_state("a")
        self.create_and_register_state("b")
        self.create_and_register_state("c")
        self.state_a = self.sm.push_state("a")
        self.state_b = self.sm.push_state("b")
        self.sm.queue_state("c")
        self.sm.update(0)

    def test_current_state(self):
        self.assertEqual(self.state_b, self.sm.current_state)

    def test_queued_not_in_active_states(self):
        active = set(i.name for i in self.sm.active_states)
        self.assertNotIn("c", active)


class EnqueueThenPop(StateManagerTestBase):
    def setUp(self):
        self.sm = StateManager("head.tail")
        self.create_and_register_state("a")
        self.create_and_register_state("b")
        self.create_and_register_state("c")
        self.state_a = self.sm.push_state("a")
        self.state_b = self.sm.push_state("b")
        self.sm.queue_state("c")
        self.sm.pop_state()
        self.sm.update(0)

    @skip("need to mock the factory")
    def test_current_state(self):
        active = list(i.name for i in self.sm.active_states if i.name == "c")
        active = list(i.name for i in self.sm.active_states)
        assert len(active) == 1
        state_c = active.pop()
        self.assertEqual(state_c, self.sm.current_state)

    @skip("need to mock the factory")
    def test_queued_not_in_active_states(self):
        active = set(i.name for i in self.sm.active_states)
        self.assertNotIn("c", active)


class WhenEmpty(StateManagerTestBase):
    def setUp(self):
        self.sm = StateManager("head.tail")

    def test_pop_raises_runtimeError(self):
        with self.assertRaises(RuntimeError):
            self.sm.pop_state()

    def test_replace_raises_runtimeError(self):
        with self.assertRaises(RuntimeError):
            self.sm.replace_state("foo")

    def test_no_states_current_state_is_none(self):
        self.assertEqual(self.sm.current_state, None)
