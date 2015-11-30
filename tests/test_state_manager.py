import unittest
import mock
import sys
import os

# for some test runners that cannot find the tuxemon core
sys.path.insert(0, os.path.join('tuxemon', ))

from core.state import StateManager
from core.state import State


def create_state(name):
    class RequiredMethodsForState(object):
        def get_event(self, event):
            pass

        def update(self, surface, keys, current_time):
            pass

    spec = type(name, (RequiredMethodsForState, State), {})
    mock_ = mock.MagicMock(spec=spec, name=name)
    mock_.__name__ = name
    return mock_


class StateManagerStackTests(unittest.TestCase):
    def setUp(self):
        self.sm = StateManager()

    def create_and_register_state(self, name):
        state = create_state(name)
        self.sm.register_state(state)
        return state

    def test_no_states_current_state_is_none(self):
        self.assertEqual(self.sm.current_state, None)

    def test_can_register_state(self):
        state = self.create_and_register_state('1')
        self.assertIn(state, self.sm.state_dict.values())

    def test_can_push_state(self):
        self.create_and_register_state('1')
        state1 = self.sm.push_state('1')
        self.assertIn(state1, self.sm.state_stack)

    def test_zero_index_is_current_state(self):
        self.create_and_register_state('1')
        state1 = self.sm.push_state('1')
        self.assertEqual(state1, self.sm.current_state)
        self.assertEqual(self.sm.state_stack[0], self.sm.current_state)

    def test_push_state_old_state_pushed_back_and_paused(self):
        self.create_and_register_state('1')
        self.create_and_register_state('2')
        state1 = self.sm.push_state('1')
        state2 = self.sm.push_state('2')

        self.assertIn(state1, self.sm.state_stack)
        self.assertEqual(self.sm.state_stack[1], state1)
        self.assertTrue(state1.pause.called)

    def test_push_state_old_state_resumes(self):
        self.create_and_register_state('1')
        self.create_and_register_state('2')
        state1 = self.sm.push_state('1')
        state2 = self.sm.push_state('2')
        self.sm.pop_state()

        self.assertTrue(state1.resume.called)

    def test_push_state_starts_state(self):
        self.create_and_register_state('1')
        state1 = self.sm.push_state('1')

        self.assertTrue(state1.startup.called)

    def test_can_pop_state(self):
        self.create_and_register_state('1')
        self.sm.push_state('1')
        self.sm.pop_state()

    def test_pop_state_removes_current_state(self):
        self.create_and_register_state('1')
        state1 = self.sm.push_state('1')
        self.sm.pop_state()

        self.assertEqual(self.sm.current_state, None)

    def test_pop_state_shutsdown_state(self):
        self.create_and_register_state('1')
        state1 = self.sm.push_state('1')
        self.sm.pop_state()

        self.assertTrue(state1.shutdown.called)

    def test_pop_empty_stack_raises_runtimeError(self):
        with self.assertRaises(RuntimeError):
            self.sm.pop_state()
