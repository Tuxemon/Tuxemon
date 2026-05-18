# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import time
from unittest.mock import MagicMock

import pytest

from tuxemon.state.queue import QueuedState, StateQueue


@pytest.fixture
def manager_ref():
    return MagicMock()


@pytest.fixture
def queue(manager_ref):
    return StateQueue(manager_ref)


def test_init(queue, manager_ref):
    assert queue._state_manager_ref is manager_ref
    assert queue._state_queue == []


def test_queue_state(queue):
    state_name = "test_state"
    kwargs = {"arg1": "value1", "arg2": "value2"}

    queue.queue_state(state_name, priority=5, **kwargs)

    expected = QueuedState(5, state_name, kwargs)
    assert queue._state_queue == [expected]


def test_handle_next_state(queue, manager_ref):
    queue.queue_state("test_state", priority=1, arg1="value1", arg2="value2")
    queue.handle_next_queued_state()

    manager_ref.replace_state.assert_called_once_with(
        "test_state", arg1="value1", arg2="value2"
    )


def test_handle_next_queued_state_no_states(queue):
    assert queue.handle_next_queued_state() is False


def test_get_queued_state_by_name(queue):
    queue.queue_state("test_state", priority=10, arg1="value1")
    result = queue.get_queued_state_by_name("test_state")

    expected = QueuedState(10, "test_state", {"arg1": "value1"})
    assert result == expected


def test_get_queued_state_by_name_not_found(queue):
    with pytest.raises(ValueError):
        queue.get_queued_state_by_name("missing_state")


def test_has_queued_states(queue):
    assert queue.has_queued_states is False
    queue.queue_state("test_state")
    assert queue.has_queued_states is True


def test_queued_states(queue):
    queue.queue_state("test_state", arg1="value1", arg2="value2")
    expected = [
        QueuedState(10, "test_state", {"arg1": "value1", "arg2": "value2"})
    ]
    assert queue.queued_states == expected


def test_queued_states_immutability(queue):
    queue.queue_state("test_state", arg="value")
    external = queue.queued_states
    external.append(QueuedState(0, "malicious", {}))

    assert len(queue.queued_states) == 1


def test_multiple_queued_states_order(queue, manager_ref):
    queue.queue_state("low", priority=10)
    queue.queue_state("high", priority=1)
    queue.queue_state("medium", priority=5)

    expected_order = ["high", "medium", "low"]

    for name in expected_order:
        queue.handle_next_queued_state()
        manager_ref.replace_state.assert_called_with(name)


def test_queue_state_no_kwargs(queue):
    queue.queue_state("simple_state", priority=3)
    expected = QueuedState(3, "simple_state", {})
    assert queue._state_queue == [expected]


def test_clear(queue):
    queue.queue_state("state1")
    queue.queue_state("state2")
    queue.clear()
    assert queue.queued_states == []


def test_remove_state_by_name(queue):
    queue.queue_state("state1")
    queue.queue_state("state2")

    queue.remove_state_by_name("state1")

    expected = [QueuedState(10, "state2", {})]
    assert queue.queued_states == expected


def test_remove_state_by_name_not_found(queue):
    queue.queue_state("state1")
    with pytest.raises(ValueError):
        queue.remove_state_by_name("missing_state")


def test_replace_queued_state(queue):
    queue.queue_state("state1", arg="old")
    queue.replace_queued_state("state1", new_kwargs={"arg": "new"})

    state = queue.get_queued_state_by_name("state1")
    assert state.kwargs["arg"] == "new"


def test_replace_queued_state_not_found(queue):
    with pytest.raises(ValueError):
        queue.replace_queued_state("missing_state", new_kwargs={"arg": "x"})


def test_peek_next(queue):
    queue.queue_state("state1", arg="peek")
    expected = QueuedState(10, "state1", {"arg": "peek"})
    assert queue.peek_next() == expected


def test_peek_next_empty(queue):
    assert queue.peek_next() is None


def test_state_not_activated_before_activation_time(queue):
    future = time.time() + 5
    queue.queue_state("future_state", activation_time=future)

    activated = queue.handle_next_queued_state()
    assert activated is False
    assert queue.has_queued_states is True


def test_state_skipped_after_expiration(queue):
    past = time.time() - 5
    queue.queue_state("expired_state", expires_at=past)

    activated = queue.handle_next_queued_state()
    assert activated is False
    assert queue.has_queued_states is True


def test_remove_expired_states(queue):
    expired = time.time() - 10
    valid = time.time() + 10

    queue.queue_state("expired_state", expires_at=expired)
    queue.queue_state("valid_state", expires_at=valid)

    queue.remove_expired_states()

    names = [s.name for s in queue.queued_states]
    assert names == ["valid_state"]


def test_state_activation_and_expiration_window(queue, manager_ref):
    now = time.time()
    activation = now + 0.01
    expires = now + 0.5

    queue.queue_state(
        "timed_state",
        activation_time=activation,
        expires_at=expires,
    )

    # too early
    assert queue.handle_next_queued_state() is False

    time.sleep(0.02)

    # now it should activate
    assert queue.handle_next_queued_state() is True
    manager_ref.replace_state.assert_called_once_with("timed_state")


def test_get_queued_states_by_source(queue):
    queue.queue_state("cutscene_1", source="cutscene")
    queue.queue_state("quest_1", source="quest")
    queue.queue_state("cutscene_2", source="cutscene")

    cutscene_states = [
        s for s in queue.queued_states if s.source == "cutscene"
    ]

    assert len(cutscene_states) == 2
    assert all(s.source == "cutscene" for s in cutscene_states)


def test_state_skipped_due_to_unmet_condition(queue):
    def condition():
        return False

    queue.queue_state("locked_state", condition=condition)

    activated = queue.handle_next_queued_state()
    assert activated is False
    assert queue.has_queued_states is True
