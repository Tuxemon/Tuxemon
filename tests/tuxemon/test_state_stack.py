# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import Mock

from tuxemon.state.stack import StateStack
from tuxemon.state.state import State


class TestStateStack(unittest.TestCase):

    def setUp(self):
        self.stack = StateStack()
        self.state = Mock(spec=State)

    def test_init(self):
        self.assertEqual(list(self.stack._stack), [])
        self.assertEqual(self.stack._resume_set, set())

    def test_push(self):
        self.stack.push(self.state)
        self.assertEqual(list(self.stack._stack), [self.state])
        self.assertIn(self.state, self.stack._resume_set)

    def test_pop(self):
        self.stack.push(self.state)
        popped_state = self.stack.pop()
        self.assertEqual(popped_state, self.state)
        self.assertEqual(list(self.stack._stack), [])

    def test_pop_with_state(self):
        state1 = Mock(spec=State)
        state2 = Mock(spec=State)
        self.stack.push(state1)
        self.stack.push(state2)
        popped_state = self.stack.pop(state1)
        self.assertEqual(popped_state, state1)
        self.assertEqual(list(self.stack._stack), [state2])

    def test_pop_empty_stack(self):
        with self.assertRaises(RuntimeError):
            self.stack.pop()

    def test_pop_state_not_found(self):
        state1 = Mock(spec=State)
        state2 = Mock(spec=State)
        self.stack.push(state1)
        with self.assertRaises(RuntimeError):
            self.stack.pop(state2)

    def test_replace(self):
        state1 = Mock(spec=State)
        state2 = Mock(spec=State)
        self.stack.push(state1)
        replaced_state = self.stack.replace(state2)
        self.assertEqual(replaced_state, state1)
        self.assertEqual(list(self.stack._stack), [state2])

    def test_replace_empty_stack(self):
        with self.assertRaises(RuntimeError):
            self.stack.replace(self.state)

    def test_mark_for_resume(self):
        self.stack.mark_for_resume(self.state)
        self.assertIn(self.state, self.stack._resume_set)

    def test_mark_resumed(self):
        self.stack.mark_for_resume(self.state)
        self.stack.mark_resumed(self.state)
        self.assertNotIn(self.state, self.stack._resume_set)

    def test_should_resume(self):
        self.stack.mark_for_resume(self.state)
        self.assertTrue(self.stack.should_resume(self.state))

    def test_remove(self):
        self.stack.push(self.state)
        self.stack.remove(self.state)
        self.assertEqual(list(self.stack._stack), [])

    def test_remove_state_not_found(self):
        with self.assertRaises(RuntimeError):
            self.stack.remove(self.state)

    def test_current(self):
        self.stack.push(self.state)
        self.assertEqual(self.stack.current(), self.state)

    def test_current_empty_stack(self):
        self.assertIsNone(self.stack.current())

    def test_all(self):
        state1 = Mock(spec=State)
        state2 = Mock(spec=State)
        self.stack.push(state1)
        self.stack.push(state2)
        self.assertEqual(self.stack.all(), [state2, state1])

    def test_get_states_by_name(self):

        class StateImpl(State):
            def __init__(self, name: str) -> None:
                self._name = name

            @property
            def name(self) -> str:
                return self._name

        state = StateImpl("test_state")
        self.stack.push(state)
        self.assertEqual(self.stack.get_states_by_name("test_state")[0], state)

    def test_get_states_by_name_not_found(self):
        with self.assertRaises(ValueError):
            self.stack.get_states_by_name("test_state")

    def test_push_duplicate_state(self):
        self.stack.push(self.state)
        self.stack.push(self.state)
        self.assertEqual(self.stack.all(), [self.state, self.state])
        self.assertIn(self.state, self.stack._resume_set)

    def test_pop_middle_state(self):
        top = Mock(spec=State)
        middle = Mock(spec=State)
        bottom = Mock(spec=State)
        self.stack.push(bottom)
        self.stack.push(middle)
        self.stack.push(top)
        popped = self.stack.pop(middle)
        self.assertEqual(popped, middle)
        self.assertEqual(self.stack.current(), top)

    def test_replace_with_same_state(self):
        self.stack.push(self.state)
        replaced = self.stack.replace(self.state)
        self.assertEqual(replaced, self.state)
        self.assertEqual(self.stack.current(), self.state)

    def test_resume_after_pop(self):
        state1 = Mock(spec=State)
        state2 = Mock(spec=State)
        self.stack.push(state2)
        self.stack.push(state1)
        self.stack.pop()
        self.assertTrue(self.stack.should_resume(state2))

    def test_remove_then_resume_check(self):
        self.stack.push(self.state)
        self.stack.remove(self.state)
        self.assertFalse(self.stack.should_resume(self.state))

    def test_get_states_by_name_multiple_matches(self):
        class NamedState(State):
            def __init__(self, name):
                self._name = name

            @property
            def name(self):
                return self._name

        state1 = NamedState("duplicate")
        state2 = NamedState("duplicate")
        self.stack.push(state2)
        self.stack.push(state1)
        found = self.stack.get_states_by_name("duplicate")
        self.assertEqual(found[0], state1)
