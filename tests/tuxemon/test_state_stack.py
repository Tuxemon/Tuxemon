# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import Mock

import pytest

from tuxemon.state.stack import StateStack
from tuxemon.state.state import State


@pytest.fixture
def stack():
    return StateStack()


@pytest.fixture
def state():
    return Mock(spec=State)


def test_init(stack):
    assert list(stack._stack) == []
    assert stack._resume_set == set()


def test_push(stack, state):
    stack.push(state)
    assert list(stack._stack) == [state]
    assert state in stack._resume_set


def test_pop(stack, state):
    stack.push(state)
    popped = stack.pop()
    assert popped is state
    assert list(stack._stack) == []


def test_pop_with_state(stack):
    s1 = Mock(spec=State)
    s2 = Mock(spec=State)
    stack.push(s1)
    stack.push(s2)

    popped = stack.pop(s1)
    assert popped is s1
    assert list(stack._stack) == [s2]


def test_pop_empty_stack(stack):
    with pytest.raises(RuntimeError):
        stack.pop()


def test_pop_state_not_found(stack):
    s1 = Mock(spec=State)
    s2 = Mock(spec=State)
    stack.push(s1)

    with pytest.raises(RuntimeError):
        stack.pop(s2)


def test_replace(stack):
    s1 = Mock(spec=State)
    s2 = Mock(spec=State)

    stack.push(s1)
    replaced = stack.replace(s2)

    assert replaced is s1
    assert list(stack._stack) == [s2]


def test_replace_empty_stack(stack, state):
    with pytest.raises(RuntimeError):
        stack.replace(state)


def test_mark_for_resume(stack, state):
    stack.mark_for_resume(state)
    assert state in stack._resume_set


def test_mark_resumed(stack, state):
    stack.mark_for_resume(state)
    stack.mark_resumed(state)
    assert state not in stack._resume_set


def test_should_resume(stack, state):
    stack.mark_for_resume(state)
    assert stack.should_resume(state) is True


def test_remove(stack, state):
    stack.push(state)
    stack.remove(state)
    assert list(stack._stack) == []


def test_remove_state_not_found(stack, state):
    with pytest.raises(RuntimeError):
        stack.remove(state)


def test_current(stack, state):
    stack.push(state)
    assert stack.current() is state


def test_current_empty(stack):
    assert stack.current() is None


def test_all(stack):
    s1 = Mock(spec=State)
    s2 = Mock(spec=State)

    stack.push(s1)
    stack.push(s2)

    assert stack.all() == [s2, s1]


def test_get_states_by_name(stack):
    class StateImpl(State):
        def __init__(self, client, name="test_state"):
            super().__init__(client)
            self._name = name

        @property
        def name(self):
            return self._name

    s = StateImpl(client=Mock())
    stack.push(s)

    assert stack.get_states_by_name("test_state")[0] is s


def test_get_states_by_name_not_found(stack):
    with pytest.raises(ValueError):
        stack.get_states_by_name("test_state")


def test_get_states_by_name_multiple_matches(stack):
    class NamedState(State):
        def __init__(self, client, name="duplicate"):
            super().__init__(client)
            self._name = name

        @property
        def name(self):
            return self._name

    s1 = NamedState(client=Mock(), name="duplicate")
    s2 = NamedState(client=Mock(), name="duplicate")

    stack.push(s2)
    stack.push(s1)

    found = stack.get_states_by_name("duplicate")
    assert found[0] is s1


def test_push_duplicate_state(stack, state):
    stack.push(state)
    stack.push(state)

    assert stack.all() == [state, state]
    assert state in stack._resume_set


def test_pop_middle_state(stack):
    top = Mock(spec=State)
    middle = Mock(spec=State)
    bottom = Mock(spec=State)

    stack.push(bottom)
    stack.push(middle)
    stack.push(top)

    popped = stack.pop(middle)

    assert popped is middle
    assert stack.current() is top


def test_replace_with_same_state(stack, state):
    stack.push(state)
    replaced = stack.replace(state)

    assert replaced is state
    assert stack.current() is state


def test_resume_after_pop(stack):
    s1 = Mock(spec=State)
    s2 = Mock(spec=State)

    stack.push(s2)
    stack.push(s1)

    stack.pop()

    assert stack.should_resume(s2) is True


def test_remove_then_resume_check(stack, state):
    stack.push(state)
    stack.remove(state)

    assert stack.should_resume(state) is False
