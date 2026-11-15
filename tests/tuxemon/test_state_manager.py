# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock, patch

import pytest

from tuxemon.event.eventbus import EventBus
from tuxemon.state.factory import StateFactory
from tuxemon.state.manager import StateManager
from tuxemon.state.repository import StateRepository
from tuxemon.state.state import State
from tuxemon.states.input import InputMenu
from tuxemon.states.world_state import WorldState


def create_state(name: str) -> MagicMock:
    mock_state = MagicMock(spec=State, name=f"mock {name}")
    mock_state.__name__ = name
    mock_state.name = name
    mock_state.return_value = mock_state
    return mock_state


@pytest.fixture
def state_manager() -> StateManager:
    mock_client = MagicMock()
    mock_client.event_bus = EventBus()
    return StateManager("head.tail", mock_client, StateRepository())


@pytest.fixture
def register_state(state_manager):
    def _register(name: str) -> MagicMock:
        state = create_state(name)
        state_manager.register_state(state)
        return state

    return _register


def perform_ops(state_manager, register_state, ops):
    """
    Helper to drive the state machine with a small DSL.
    """
    states: dict[str, MagicMock] = {}

    for op in ops:
        parts = op.split(":", 1)
        cmd = parts[0]
        arg = parts[1] if len(parts) == 2 else None

        if cmd in {"push", "queue", "replace"} and arg is not None:
            if arg not in states:
                states[arg] = register_state(arg)

        if cmd == "push" and arg is not None:
            state_manager.push_state(arg)
        elif cmd == "queue" and arg is not None:
            state_manager.queue_state(arg)
        elif cmd == "replace" and arg is not None:
            state_manager.replace_state(arg)
        elif cmd == "pop":
            if arg is None:
                state_manager.pop_state()
            else:
                state_manager.pop_state(states[arg])
        elif cmd == "update":
            state_manager.update(0)

    return states


@pytest.mark.parametrize(
    "ops, expected_current, expected_active, expected_calls",
    [
        pytest.param(
            ["push:a", "update"],
            "a",
            {"a"},
            {"a": {"resume": 1, "pause": 0, "shutdown": 0}},
            id="push_when_empty",
        ),
        pytest.param(
            ["push:a", "push:b", "update"],
            "b",
            {"a", "b"},
            {
                "a": {"resume": 1, "pause": 1, "shutdown": 0},
                "b": {"resume": 1, "pause": 0, "shutdown": 0},
            },
            id="push_when_not_empty",
        ),
    ],
)
def test_push_behavior(
    state_manager,
    register_state,
    ops,
    expected_current,
    expected_active,
    expected_calls,
):
    states = perform_ops(state_manager, register_state, ops)

    assert state_manager.current_state is states[expected_current]
    active_names = {s.name for s in state_manager.active_states}
    assert active_names == expected_active

    for name, calls in expected_calls.items():
        s = states[name]
        assert s.resume.call_count == calls["resume"]
        assert s.pause.call_count == calls["pause"]
        assert s.shutdown.call_count == calls["shutdown"]


@pytest.mark.parametrize(
    "ops, expected_current, expected_active, expected_calls",
    [
        pytest.param(
            ["push:a", "push:b", "pop", "update"],
            "a",
            {"a"},
            {
                "a": {"resume": 2, "pause": 1, "shutdown": 0},
                "b": {"resume": 1, "pause": 1, "shutdown": 1},
            },
            id="pop_state",
        ),
        pytest.param(
            ["push:a", "push:b", "pop:b", "update"],
            "a",
            {"a"},
            {
                "a": {"resume": 2, "pause": 1, "shutdown": 0},
                "b": {"resume": 1, "pause": 1, "shutdown": 1},
            },
            id="remove_when_current",
        ),
        pytest.param(
            ["push:a", "push:b", "pop:a", "update"],
            "b",
            {"b"},
            {
                "a": {"resume": 1, "pause": 1, "shutdown": 1},
                "b": {"resume": 1, "pause": 0, "shutdown": 0},
            },
            id="remove_when_not_current",
        ),
    ],
)
def test_pop_behavior(
    state_manager,
    register_state,
    ops,
    expected_current,
    expected_active,
    expected_calls,
):
    states = perform_ops(state_manager, register_state, ops)

    assert state_manager.current_state is states[expected_current]
    active_names = {s.name for s in state_manager.active_states}
    assert active_names == expected_active

    for name, calls in expected_calls.items():
        s = states[name]
        assert s.resume.call_count == calls["resume"]
        assert s.pause.call_count == calls["pause"]
        assert s.shutdown.call_count == calls["shutdown"]


@pytest.mark.parametrize(
    "ops, expected_current, expected_active, shutdown_states, resumed_states",
    [
        pytest.param(
            ["push:a", "replace:b", "update"],
            "b",
            {"b"},
            {"a"},
            {"b"},
            id="replace_single",
        ),
        pytest.param(
            ["push:a", "push:b", "replace:c", "update"],
            "c",
            {"a", "c"},
            {"b"},
            {"c"},
            id="replace_with_multiple_states",
        ),
    ],
)
def test_replace_behavior(
    state_manager,
    register_state,
    ops,
    expected_current,
    expected_active,
    shutdown_states,
    resumed_states,
):
    states = perform_ops(state_manager, register_state, ops)

    assert state_manager.current_state is states[expected_current]
    active_names = {s.name for s in state_manager.active_states}
    assert active_names == expected_active

    for name in shutdown_states:
        s = states[name]
        assert s.shutdown.call_count == 1

    for name in resumed_states:
        s = states[name]
        assert s.resume.call_count >= 1


@pytest.mark.parametrize(
    "ops, must_have, must_not_have, one_of",
    [
        pytest.param(
            ["push:a", "push:b", "queue:c", "update"],
            {"a", "b"},
            {"c"},
            None,
            id="enqueue_state_not_activated_until_pop",
        ),
        pytest.param(
            ["push:a", "push:b", "queue:c", "pop", "update"],
            {"a", "c"},
            set(),
            None,
            id="enqueue_then_pop",
        ),
        pytest.param(
            [
                "push:a",
                "push:b",
                "queue:c",
                "queue:d",
                "update",
                "pop",
                "update",
            ],
            {"a"},
            set(),
            {"c", "d"},
            id="multiple_queued_states",
        ),
    ],
)
def test_queue_behavior(
    state_manager, register_state, ops, must_have, must_not_have, one_of
):
    perform_ops(state_manager, register_state, ops)

    active_names = {s.name for s in state_manager.active_states}

    for name in must_have:
        assert name in active_names

    for name in must_not_have:
        assert name not in active_names

    if one_of is not None:
        assert any(name in active_names for name in one_of)


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


@pytest.mark.parametrize(
    "op, args, expected_exception",
    [
        pytest.param("pop", (), RuntimeError, id="pop_when_empty_raises"),
        pytest.param(
            "replace", ("foo",), RuntimeError, id="replace_when_empty_raises"
        ),
    ],
)
def test_when_empty_raises(state_manager, op, args, expected_exception):
    with pytest.raises(expected_exception):
        if op == "pop":
            state_manager.pop_state()
        elif op == "replace":
            state_manager.replace_state(*args)


def test_when_empty_current_state_is_none(state_manager):
    assert state_manager.current_state is None


@pytest.fixture
def resume_state_manager():
    mock_client = MagicMock()
    mock_client.event_bus = EventBus()
    sm = StateManager("game", mock_client, StateRepository())

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


@pytest.mark.parametrize(
    "ops, expect_world_resume_called",
    [
        pytest.param(
            ["push_input_menu", "input_confirm", "update"],
            True,
            id="resume_called_when_popping_input_menu_via_confirm",
        ),
        pytest.param(
            ["push_input_menu", "pop", "update"],
            True,
            id="resume_called_when_popping_state_directly",
        ),
    ],
)
def test_resume_behavior(
    resume_state_manager, ops, expect_world_resume_called
):
    sm, world_state, input_menu = resume_state_manager

    for op in ops:
        if op == "push_input_menu":
            sm.push_state(input_menu)
        elif op == "input_confirm":
            input_menu.confirm()
        elif op == "pop":
            sm.pop_state()
        elif op == "update":
            sm.update(0.1)

    if expect_world_resume_called:
        world_state.resume.assert_called()
    else:
        world_state.resume.assert_not_called()


@pytest.mark.parametrize(
    "first, second",
    [
        pytest.param("a", "b", id="push_pop_a_b"),
        pytest.param("alpha", "beta", id="push_pop_alpha_beta"),
        pytest.param("state1", "state2", id="push_pop_state1_state2"),
    ],
)
def test_push_pop_parametrized(state_manager, register_state, first, second):
    states = perform_ops(
        state_manager,
        register_state,
        [f"push:{first}", f"push:{second}", "update", "pop", "update"],
    )

    s1 = states[first]
    s2 = states[second]

    assert state_manager.current_state is s1
    assert s2 not in state_manager.active_states
    assert s1 in state_manager.active_states


def test_active_states_order(state_manager, register_state):
    perform_ops(
        state_manager,
        register_state,
        ["push:a", "push:b", "push:c", "update"],
    )

    names = [s.name for s in state_manager.active_states]
    assert names == ["c", "b", "a"]

    state_manager.pop_state()
    state_manager.update(0)
    names = [s.name for s in state_manager.active_states]
    assert names == ["b", "a"]


def test_pop_until_empty_then_push_again(state_manager, register_state):
    perform_ops(
        state_manager,
        register_state,
        ["push:a", "push:b", "pop", "pop", "update"],
    )

    assert state_manager.current_state is None
    assert not state_manager.active_states

    states = perform_ops(
        state_manager,
        register_state,
        ["push:c", "update"],
    )

    pushed = states["c"]
    assert state_manager.current_state is pushed
    assert pushed in state_manager.active_states


def test_queued_state_expires(state_manager, register_state):
    register_state("a")
    state_manager.queue_state("a", expires_at=0)
    state_manager.state_queue.remove_expired_states()
    assert not state_manager.queued_states


def test_queued_state_condition_false(state_manager, register_state):
    register_state("a")
    register_state("b")

    state_manager.push_state("a")
    state_manager.queue_state("b", condition=lambda: False)

    state_manager.pop_state()
    state_manager.update(0)

    active = {s.name for s in state_manager.active_states}
    assert "b" not in active
    assert "a" in active


def test_replace_queued_state(state_manager, register_state):
    register_state("a")
    state_manager.queue_state("a", foo=1)
    state_manager.replace_queued_state("a", new_kwargs={"foo": 999})

    queued = state_manager.get_queued_state_by_name("a")
    assert queued.kwargs["foo"] == 999


def test_remove_queued_state_by_name(state_manager, register_state):
    register_state("a")
    register_state("b")

    state_manager.queue_state("a")
    state_manager.queue_state("b")

    state_manager.remove_queued_state_by_name("a")

    names = [q.name for q in state_manager.queued_states]
    assert names == ["b"]


def test_peek_next_queued_state(state_manager, register_state):
    register_state("a")
    register_state("b")

    state_manager.queue_state("a", priority=5)
    state_manager.queue_state("b", priority=1)

    peeked = state_manager.peek_next_queued_state()
    assert peeked.name == "b"


def test_remove_state_by_name_middle(state_manager, register_state):
    register_state("a")
    b = register_state("b")
    register_state("c")

    state_manager.push_state("a")
    state_manager.push_state("b")
    state_manager.push_state("c")

    state_manager.remove_state_by_name("b")

    active = [s.name for s in state_manager.active_states]
    assert active == ["c", "a"]
    assert b.shutdown.call_count == 1


def test_remove_state_by_name_current(state_manager, register_state):
    a = register_state("a")
    b = register_state("b")

    state_manager.push_state("a")
    state_manager.push_state("b")

    state_manager.remove_state_by_name("b")

    active = [s.name for s in state_manager.active_states]
    assert active == ["a"]
    assert b.shutdown.call_count == 1
    assert a.resume.call_count >= 1


def test_resume_only_once(state_manager, register_state):
    a = register_state("a")

    state_manager.push_state("a")
    state_manager.update(0)
    state_manager.update(0)

    assert a.resume.call_count == 1


def test_resume_after_replace(state_manager, register_state):
    register_state("a")
    b = register_state("b")

    state_manager.push_state("a")
    state_manager.replace_state("b")
    state_manager.update(0)

    assert b.resume.call_count == 1


def test_pop_with_queue_activates_queued(state_manager, register_state):
    register_state("a")
    b = register_state("b")
    register_state("c")

    state_manager.push_state("a")
    state_manager.push_state("b")
    state_manager.queue_state("c")

    state_manager.pop_state(b)
    state_manager.update(0)

    active = {s.name for s in state_manager.active_states}
    assert "c" in active
    assert "a" in active
    assert "b" not in active


def test_get_state_by_name_missing_raises(state_manager, register_state):
    register_state("a")
    state_manager.push_state("a")

    with pytest.raises(ValueError):
        state_manager.get_state_by_name("MissingState")


def test_base_map_state_helpers(state_manager, register_state):
    register_state("a")
    register_state("b")
    register_state("c")

    state_manager.push_state("a")
    state_manager.push_state("b")

    assert state_manager.is_in_base_map_state()
    assert not state_manager.has_extra_states()

    state_manager.push_state("c")
    assert state_manager.has_extra_states()
