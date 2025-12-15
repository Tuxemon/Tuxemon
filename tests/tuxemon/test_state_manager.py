# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock, patch

import pytest

from tuxemon.event.eventbus import EventBus
from tuxemon.menu.input import InputMenu
from tuxemon.state.factory import StateFactory
from tuxemon.state.manager import StateManager
from tuxemon.state.repository import StateRepository
from tuxemon.state.state import State
from tuxemon.states.world_state import WorldState


def create_state(name):
    mock_state = MagicMock(spec=State, name=f"mock {name}")
    mock_state.__name__ = name
    mock_state.name = name
    mock_state.return_value = mock_state
    return mock_state


@pytest.fixture
def state_manager():
    return StateManager("head.tail", EventBus(), StateRepository())


@pytest.fixture
def register_state(state_manager):
    def _register(name):
        state = create_state(name)
        state_manager.register_state(state)
        return state

    return _register


# PushWhenEmpty
def test_push_when_empty(state_manager, register_state):
    state_a = register_state("a")
    pushed = state_manager.push_state("a")
    state_manager.update(0)

    assert pushed == state_manager.current_state
    assert pushed in state_manager.active_states
    assert pushed.resume.call_count == 1
    assert pushed.pause.call_count == 0
    assert pushed.shutdown.call_count == 0


# PushWhenNotEmpty
def test_push_when_not_empty(state_manager, register_state):
    state_a = register_state("a")
    state_b = register_state("b")

    pushed_a = state_manager.push_state("a")
    pushed_b = state_manager.push_state("b")
    state_manager.update(0)

    assert state_manager.current_state == pushed_b
    assert pushed_b in state_manager.active_states
    assert pushed_a in state_manager.active_states

    assert pushed_b.resume.call_count == 1
    assert pushed_b.pause.call_count == 0
    assert pushed_b.shutdown.call_count == 0

    assert pushed_a.resume.call_count == 1
    assert pushed_a.pause.call_count == 1
    assert pushed_a.shutdown.call_count == 0


# Pop
def test_pop_state(state_manager, register_state):
    state_a = register_state("a")
    state_b = register_state("b")

    pushed_a = state_manager.push_state("a")
    pushed_b = state_manager.push_state("b")

    state_manager.pop_state()
    state_manager.update(0)

    assert state_manager.current_state == pushed_a
    assert pushed_b not in state_manager.active_states
    assert pushed_a in state_manager.active_states

    assert pushed_b.resume.call_count == 1
    assert pushed_b.pause.call_count == 1
    assert pushed_b.shutdown.call_count == 1

    assert pushed_a.resume.call_count == 2
    assert pushed_a.pause.call_count == 1
    assert pushed_a.shutdown.call_count == 0


# Resume
def test_resume_called(state_manager, register_state):
    state_a = register_state("a")
    pushed_a = state_manager.push_state("a")

    assert pushed_a.update.call_count == 0
    assert pushed_a.resume.call_count == 0

    state_manager.update(0)
    assert pushed_a.update.call_count == 1
    assert pushed_a.resume.call_count == 1

    state_b = register_state("b")
    pushed_b = state_manager.push_state("b")
    state_manager.pop_state()
    state_manager.update(0)

    assert pushed_a.update.call_count == 2
    assert pushed_a.resume.call_count == 2
    assert pushed_a.pause.call_count == 1


# RemoveWhenCurrent
def test_remove_when_current(state_manager, register_state):
    state_a = register_state("a")
    state_b = register_state("b")

    pushed_a = state_manager.push_state("a")
    pushed_b = state_manager.push_state("b")

    state_manager.pop_state(pushed_b)
    state_manager.update(0)

    assert state_manager.current_state == pushed_a
    assert pushed_b not in state_manager.active_states
    assert pushed_a in state_manager.active_states

    assert pushed_b.shutdown.call_count == 1
    assert pushed_a.resume.call_count == 2


# RemoveWhenNotCurrent
def test_remove_when_not_current(state_manager, register_state):
    state_a = register_state("a")
    state_b = register_state("b")

    pushed_a = state_manager.push_state("a")
    pushed_b = state_manager.push_state("b")

    state_manager.pop_state(pushed_a)
    state_manager.update(0)

    assert state_manager.current_state == pushed_b
    assert pushed_a not in state_manager.active_states
    assert pushed_b in state_manager.active_states

    assert pushed_a.shutdown.call_count == 1
    assert pushed_b.resume.call_count == 1


# Replace
def test_replace_state(state_manager, register_state):
    state_a = register_state("a")
    state_b = register_state("b")

    pushed_a = state_manager.push_state("a")
    pushed_b = state_manager.replace_state("b")
    state_manager.update(0)

    assert state_manager.current_state == pushed_b
    assert pushed_b in state_manager.active_states
    assert pushed_a not in state_manager.active_states

    assert pushed_a.shutdown.call_count == 1
    assert pushed_b.resume.call_count == 1


# Enqueue
def test_enqueue_state(state_manager, register_state):
    state_a = register_state("a")
    state_b = register_state("b")
    state_c = register_state("c")

    pushed_a = state_manager.push_state("a")
    pushed_b = state_manager.push_state("b")
    state_manager.queue_state("c")
    state_manager.update(0)

    assert state_manager.current_state == pushed_b
    active_names = {s.name for s in state_manager.active_states}
    assert "c" not in active_names


# EnqueueThenPop
def test_enqueue_then_pop(state_manager, register_state):
    state_a = register_state("a")
    state_b = register_state("b")
    state_c = register_state("c")

    state_manager.push_state("a")
    state_manager.push_state("b")
    state_manager.queue_state("c")
    state_manager.pop_state()
    state_manager.update(0)

    active_names = {s.name for s in state_manager.active_states}
    assert "c" in active_names
    assert "a" in active_names


@patch.object(StateFactory, "create_state")
def test_enqueue_then_pop_current_state(
    mock_instance, state_manager, register_state
):
    mock_state_c = register_state("c")
    mock_instance.return_value = mock_state_c

    while state_manager.active_states:
        state_manager.pop_state()

    state_manager.push_state("c")

    assert mock_state_c in state_manager.active_states
    active = [s.name for s in state_manager.active_states]
    assert active == ["c"]


# WhenEmpty
def test_when_empty_pop_raises(state_manager):
    with pytest.raises(RuntimeError):
        state_manager.pop_state()


def test_when_empty_replace_raises(state_manager):
    with pytest.raises(RuntimeError):
        state_manager.replace_state("foo")


def test_when_empty_current_state_is_none(state_manager):
    assert state_manager.current_state is None


# TestStateManagerResumeCallCount
@pytest.fixture
def resume_state_manager():
    sm = StateManager("game", EventBus(), StateRepository())

    world_state = MagicMock(spec=WorldState)
    world_state.__name__ = "WorldState"
    world_state.name = "WorldState"

    input_menu = MagicMock(spec=InputMenu)
    input_menu.__name__ = "InputMenu"
    input_menu.name = "InputMenu"

    sm.register_state(world_state)
    sm.register_state(input_menu)
    sm.push_state(world_state)

    return sm, world_state, input_menu


def test_resume_called_when_popping_input_menu(resume_state_manager):
    sm, world_state, input_menu = resume_state_manager
    sm.push_state(input_menu)
    input_menu.confirm()
    sm.update(0.1)
    world_state.resume.assert_called()


def test_resume_called_when_popping_state(resume_state_manager):
    sm, world_state, input_menu = resume_state_manager
    sm.push_state(input_menu)
    sm.pop_state()
    world_state.resume.assert_called()


# Parametrize Push/Pop
@pytest.mark.parametrize(
    "first,second",
    [
        ("a", "b"),
        ("alpha", "beta"),
        ("state1", "state2"),
    ],
)
def test_push_pop_parametrized(state_manager, register_state, first, second):
    s1 = register_state(first)
    s2 = register_state(second)

    pushed1 = state_manager.push_state(first)
    pushed2 = state_manager.push_state(second)
    state_manager.update(0)

    assert state_manager.current_state == pushed2
    assert pushed2 in state_manager.active_states
    assert pushed1 in state_manager.active_states

    state_manager.pop_state()
    state_manager.update(0)

    assert state_manager.current_state == pushed1
    assert pushed2 not in state_manager.active_states
    assert pushed1 in state_manager.active_states


# Edge Case: Multiple Queued States
def test_multiple_queued_states(state_manager, register_state):
    s1 = register_state("a")
    s2 = register_state("b")
    s3 = register_state("c")
    s4 = register_state("d")

    state_manager.push_state("a")
    state_manager.push_state("b")
    state_manager.queue_state("c")
    state_manager.queue_state("d")
    state_manager.update(0)

    active_names = {s.__name__ for s in state_manager.active_states}
    assert "c" not in active_names
    assert "d" not in active_names

    state_manager.pop_state()
    state_manager.update(0)
    active_names = {s.__name__ for s in state_manager.active_states}
    assert "c" in active_names or "d" in active_names


# Edge Case: Replace When Stack Has >1 States
def test_replace_with_multiple_states(state_manager, register_state):
    s1 = register_state("a")
    s2 = register_state("b")
    s3 = register_state("c")

    state_manager.push_state("a")
    state_manager.push_state("b")
    replaced = state_manager.replace_state("c")
    state_manager.update(0)

    assert state_manager.current_state == replaced
    active_names = [s.__name__ for s in state_manager.active_states]
    assert "c" in active_names
    assert "b" not in active_names
    assert "a" in active_names


# Edge Case: Popping Until Empty and Then Pushing Again
def test_pop_until_empty_then_push_again(state_manager, register_state):
    s1 = register_state("a")
    s2 = register_state("b")

    state_manager.push_state("a")
    state_manager.push_state("b")

    state_manager.pop_state()
    state_manager.pop_state()
    state_manager.update(0)

    assert state_manager.current_state is None
    assert not state_manager.active_states

    s3 = register_state("c")
    pushed = state_manager.push_state("c")
    state_manager.update(0)

    assert state_manager.current_state == pushed
    assert pushed in state_manager.active_states


# Integration Check: Active States Order
def test_active_states_order(state_manager, register_state):
    s1 = register_state("a")
    s2 = register_state("b")
    s3 = register_state("c")

    state_manager.push_state("a")
    state_manager.push_state("b")
    state_manager.push_state("c")
    state_manager.update(0)

    names = [s.name for s in state_manager.active_states]
    assert names == ["c", "b", "a"]

    state_manager.pop_state()
    state_manager.update(0)
    names = [s.name for s in state_manager.active_states]
    assert names == ["b", "a"]
