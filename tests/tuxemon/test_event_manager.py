# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import Mock

import pytest

from tuxemon.event.eventbus import EventBus
from tuxemon.event.eventmanager import EventManager
from tuxemon.platform.events import PlayerInput
from tuxemon.state.manager import StateManager


@pytest.fixture
def event_bus():
    return Mock(spec=EventBus)


@pytest.fixture
def state_manager():
    return Mock(spec=StateManager)


@pytest.fixture
def event_manager(event_bus, state_manager):
    return EventManager(event_bus, state_manager)


def test_init(event_manager, state_manager):
    assert event_manager._state_manager is state_manager


@pytest.mark.parametrize(
    "events, active_states, expected_len",
    [
        pytest.param([], [], 0, id="no_events"),
        pytest.param(
            [Mock(spec=PlayerInput), Mock(spec=PlayerInput)],
            [],
            2,
            id="two_events_no_states",
        ),
        pytest.param(
            [Mock(spec=PlayerInput), Mock(spec=PlayerInput)],
            [Mock()],
            2,
            id="two_events_with_state",
        ),
    ],
)
def test_process_events(
    event_manager, state_manager, events, active_states, expected_len
):
    if active_states:
        state = active_states[0]
        state.process_event = Mock(return_value=Mock(spec=PlayerInput))
        state_manager.active_states = active_states
    else:
        state_manager.active_states = []

    result = list(event_manager.process_events(events))
    assert len(result) == expected_len


@pytest.mark.parametrize(
    "processed_return, expected",
    [
        pytest.param(None, None, id="absorbed"),
        pytest.param("same", "same", id="same_event"),
        pytest.param("modified", "modified", id="modified_event"),
    ],
)
def test_propagate_event(
    event_manager, state_manager, processed_return, expected
):
    event = Mock(spec=PlayerInput)
    state = Mock()

    if processed_return == "same":
        state.process_event = Mock(return_value=event)
        expected = event
    elif processed_return == "modified":
        processed_event = Mock(spec=PlayerInput)
        state.process_event = Mock(return_value=processed_event)
        expected = processed_event
    else:
        state.process_event = Mock(return_value=None)

    state_manager.active_states = [state]
    result = event_manager.propagate_event(event)
    assert result is expected


def test_release_controls(event_manager, state_manager):
    input_manager = Mock()
    input_manager.event_queue.release_controls.return_value = [
        Mock(spec=PlayerInput),
        Mock(spec=PlayerInput),
    ]
    state_manager.active_states = []
    result = event_manager.release_controls(input_manager)
    assert result == list(
        event_manager.process_events(
            input_manager.event_queue.release_controls.return_value
        )
    )


def test_middleware_preprocess_consumes_event(event_manager):
    mw = Mock()
    mw.preprocess.return_value = None
    mw.postprocess.return_value = None
    event_manager.add_middleware(mw)

    events = [Mock(spec=PlayerInput)]
    result = list(event_manager.process_events(events))

    assert result == []
    mw.preprocess.assert_called_once()


def test_middleware_preprocess_modifies_event(event_manager, state_manager):
    modified_event = Mock(spec=PlayerInput)
    mw = Mock()
    mw.preprocess.return_value = modified_event
    mw.postprocess.return_value = modified_event
    event_manager.add_middleware(mw)

    events = [Mock(spec=PlayerInput)]
    state_manager.active_states = []
    result = list(event_manager.process_events(events))

    assert result == [modified_event]
    mw.preprocess.assert_called_once()
    mw.postprocess.assert_called_once()


def test_middleware_postprocess_consumes_event(event_manager, state_manager):
    mw = Mock()
    mw.preprocess.side_effect = lambda e: e
    mw.postprocess.return_value = None
    event_manager.add_middleware(mw)

    events = [Mock(spec=PlayerInput)]
    state_manager.active_states = []
    result = list(event_manager.process_events(events))

    assert result == []
    mw.postprocess.assert_called_once()


def test_multiple_middleware_chain(event_manager, state_manager):
    mw1 = Mock()
    mw1.preprocess.side_effect = lambda e: e
    mw1.postprocess.side_effect = lambda e: e

    mw2 = Mock()
    mw2.preprocess.side_effect = lambda e: e
    mw2.postprocess.side_effect = lambda e: None

    event_manager.add_middleware(mw1)
    event_manager.add_middleware(mw2)

    events = [Mock(spec=PlayerInput)]
    state_manager.active_states = []
    result = list(event_manager.process_events(events))

    assert result == []
    mw1.preprocess.assert_called_once()
    mw2.preprocess.assert_called_once()
    mw2.postprocess.assert_called_once()


def test_add_and_remove_middleware(event_manager):
    mw = Mock()
    event_manager.add_middleware(mw)
    assert any(inst is mw for _, inst in event_manager.middleware.values())

    event_manager.remove_middleware(mw)
    assert all(inst is not mw for _, inst in event_manager.middleware.values())


def test_empty_event_list(event_manager):
    assert list(event_manager.process_events([])) == []


def test_state_absorbs_event(event_manager, state_manager):
    event = Mock(spec=PlayerInput)
    state = Mock()
    state.process_event.return_value = None
    state_manager.active_states = [state]

    result = list(event_manager.process_events([event]))
    assert result == []


def test_state_modifies_event(event_manager, state_manager):
    event = Mock(spec=PlayerInput)
    modified_event = Mock(spec=PlayerInput)
    state = Mock()
    state.process_event.return_value = modified_event
    state_manager.active_states = [state]

    result = list(event_manager.process_events([event]))
    assert result == [modified_event]
