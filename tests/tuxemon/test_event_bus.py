# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock

import pytest

from tuxemon.event.eventbus import EventBus, Listener
from tuxemon.state.manager import StateManager
from tuxemon.state.repository import StateRepository


@pytest.fixture
def event_bus():
    return EventBus()


@pytest.fixture
def callbacks():
    return MagicMock(), MagicMock(), MagicMock()


@pytest.fixture
def state_manager():
    mock_client = MagicMock()
    mock_client.event_bus = EventBus()
    return StateManager("test", mock_client, StateRepository())


def test_register_event(event_bus, callbacks):
    cb, _, _ = callbacks
    event_bus.subscribe("test_event", cb, priority=10)
    assert "test_event" in event_bus._listeners
    assert event_bus._listeners["test_event"] == [Listener(10, cb)]


def test_unregister_event(event_bus, callbacks):
    cb, _, _ = callbacks
    event_bus.subscribe("test_event", cb, priority=10)
    event_bus.unsubscribe("test_event", cb)
    assert "test_event" not in event_bus._listeners


def test_unregister_event_with_priority(event_bus, callbacks):
    cb, _, _ = callbacks
    event_bus.subscribe("test_event", cb, priority=10)
    event_bus.subscribe("test_event", cb, priority=5)
    event_bus.unsubscribe("test_event", cb, priority=10)
    assert "test_event" in event_bus._listeners
    assert event_bus._listeners["test_event"] == [Listener(5, cb)]


def test_trigger_event(event_bus, callbacks):
    cb, _, _ = callbacks
    event_bus.subscribe("test_event", cb, priority=10)
    event_bus.publish("test_event", "arg1", kwarg1="value1")
    cb.assert_called_once_with("arg1", kwarg1="value1")


def test_reset_events(event_bus, callbacks):
    cb, _, _ = callbacks
    event_bus.subscribe("test_event", cb, priority=10)
    assert event_bus._listeners
    event_bus.reset_all_events()
    assert not event_bus._listeners


def test_unregister_nonexistent_event(event_bus, callbacks):
    cb, _, _ = callbacks
    event_bus.unsubscribe("nonexistent_event", cb)


def test_multiple_callbacks_priority_order(event_bus):
    calls = []

    def cb1(*args, **kwargs):
        calls.append("cb1")

    def cb2(*args, **kwargs):
        calls.append("cb2")

    event_bus.subscribe("test_event", cb1, priority=5)
    event_bus.subscribe("test_event", cb2, priority=10)
    event_bus.publish("test_event")
    assert calls == ["cb2", "cb1"]


def test_publish_no_listeners(event_bus):
    event_bus.publish("no_listeners_event")


def test_duplicate_callback_registration(event_bus, callbacks):
    cb, _, _ = callbacks
    event_bus.subscribe("test_event", cb, priority=10)
    event_bus.subscribe("test_event", cb, priority=5)
    listeners = event_bus._listeners["test_event"]
    assert len(listeners) == 2
    assert Listener(10, cb) in listeners
    assert Listener(5, cb) in listeners


def test_listener_sorting_stability_same_priority(event_bus):
    calls = []

    def cb1(*args, **kwargs):
        calls.append("cb1")

    def cb2(*args, **kwargs):
        calls.append("cb2")

    event_bus.subscribe("test_event", cb1, priority=5)
    event_bus.subscribe("test_event", cb2, priority=5)
    event_bus.publish("test_event")
    assert calls == ["cb1", "cb2"]


def test_callback_exception_handling(event_bus):
    def faulty(*args, **kwargs):
        raise RuntimeError("boom")

    safe = MagicMock()
    event_bus.subscribe("test_event", faulty, priority=10)
    event_bus.subscribe("test_event", safe, priority=5)
    event_bus.publish("test_event", "arg")
    safe.assert_called_once_with("arg")


def test_listener_identity_distinction(event_bus):
    def cb1(*args, **kwargs):
        pass

    def cb2(*args, **kwargs):
        pass

    event_bus.subscribe("test_event", cb1, priority=5)
    event_bus.subscribe("test_event", cb2, priority=5)
    listeners = event_bus._listeners["test_event"]
    assert len(listeners) == 2
    assert listeners[0].callback is not listeners[1].callback


def test_global_events(state_manager, callbacks):
    cb, _, _ = callbacks
    state_manager.register_global_event("pre_state_update", cb)
    state_manager.update(0.1)
    cb.assert_called_once_with(0.1)
    cb.reset_mock()
    state_manager.register_global_event("post_state_update", cb)
    state_manager.update(0.1)
    cb.assert_called()
    cb.reset_mock()
    state_manager.unregister_global_event("pre_state_update", cb)
    state_manager.update(0.1)
    cb.assert_called_once_with(0.1)


def test_global_events_multiple_callbacks(state_manager, callbacks):
    cb1, cb2, _ = callbacks
    state_manager.register_global_event("pre_state_update", cb1)
    state_manager.register_global_event("pre_state_update", cb2)
    state_manager.update(0.1)
    cb1.assert_called_once_with(0.1)
    cb2.assert_called_once_with(0.1)


def test_global_events_unregister_nonexistent(state_manager, callbacks):
    cb, _, _ = callbacks
    state_manager.event_bus.reset_all_events()
    state_manager.unregister_global_event("pre_state_update", cb)


def test_global_events_unregister_correct_callback(state_manager, callbacks):
    cb1, cb2, _ = callbacks
    state_manager.register_global_event("pre_state_update", cb1)
    state_manager.register_global_event("pre_state_update", cb2)
    state_manager.unregister_global_event("pre_state_update", cb1)
    state_manager.update(0.1)
    cb1.assert_not_called()
    cb2.assert_called_once()


def test_state_manager_event_isolation(callbacks):
    cb1, cb2, _ = callbacks
    mock_client1 = MagicMock()
    mock_client1.event_bus = EventBus()
    mock_client2 = MagicMock()
    mock_client2.event_bus = EventBus()
    manager1 = StateManager("test1", mock_client1, StateRepository())
    manager2 = StateManager("test2", mock_client2, StateRepository())
    manager1.register_global_event("pre_state_update", cb1)
    manager2.register_global_event("pre_state_update", cb2)
    manager1.update(0.1)
    manager2.update(0.1)
    cb1.assert_called_once_with(0.1)
    cb2.assert_called_once_with(0.1)
