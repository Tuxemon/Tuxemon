# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import Mock

import pytest

from tuxemon.event.eventaction import EventAction
from tuxemon.event.eventengine import EventState, RunningEvent


class DummyAction(EventAction):
    name = "dummy"

    def start(self, session):
        pass


@pytest.fixture
def simple_event():
    return Mock(
        id=1,
        priority=5,
        delay=None,
        timeout=None,
    )


@pytest.fixture
def expanded_actions():
    return [1, 2, 3]


def test_init(simple_event, expanded_actions):
    event = RunningEvent(simple_event, expanded_actions)

    assert event.map_event is simple_event
    assert event.actions == expanded_actions
    assert event.context == {}
    assert event.action_index == 0
    assert event.current_action is None
    assert event.state == EventState.WAITING
    assert event.elapsed_time == 0.0


def test_get_next_action(simple_event, expanded_actions):
    event = RunningEvent(simple_event, expanded_actions)

    assert event.get_next_action() == 1
    event.advance()
    assert event.get_next_action() == 2
    event.advance()
    assert event.get_next_action() == 3
    event.advance()
    assert event.get_next_action() is None


def test_advance(simple_event, expanded_actions):
    event = RunningEvent(simple_event, expanded_actions)

    event.advance()
    assert event.action_index == 1

    event.advance()
    assert event.action_index == 2

    event.advance()
    assert event.action_index == 3


def test_cancel(simple_event, expanded_actions):
    event = RunningEvent(simple_event, expanded_actions)
    event.cancel()

    assert event.state == EventState.CANCELLED
    assert event.is_cancelled()


def test_context(simple_event, expanded_actions):
    event = RunningEvent(simple_event, expanded_actions)

    event.context["a"] = 1
    assert event.context == {"a": 1}


def test_state_transitions(simple_event, expanded_actions):
    event = RunningEvent(simple_event, expanded_actions)

    assert event.state == EventState.WAITING

    event.running()
    assert event.state == EventState.RUNNING
    assert event.is_running()

    event.cancel()
    assert event.state == EventState.CANCELLED
    assert event.is_cancelled()


def test_tick_accumulates_elapsed_time(simple_event, expanded_actions):
    event = RunningEvent(simple_event, expanded_actions)

    assert event.elapsed_time == 0.0
    assert event.tick(1.5)
    assert event.elapsed_time == pytest.approx(1.5)

    assert event.tick(2.0)
    assert event.elapsed_time == pytest.approx(3.5)


def test_tick_respects_delay(expanded_actions):
    map_event = Mock(id=1, priority=5, timeout=None, delay=3.0)
    event = RunningEvent(map_event, expanded_actions)

    assert not event.tick(2.0)
    assert event.elapsed_time == 2.0

    assert event.tick(2.0)
    assert event.elapsed_time == 4.0


def test_tick_respects_timeout(expanded_actions):
    map_event = Mock(id=1, priority=5, timeout=5.0, delay=None)
    event = RunningEvent(map_event, expanded_actions)

    assert event.tick(4.0)
    assert not event.is_cancelled()

    assert not event.tick(2.0)
    assert event.is_cancelled()


def test_tick_delay_and_timeout_combined(expanded_actions):
    map_event = Mock(id=1, priority=5, timeout=8.0, delay=3.0)
    event = RunningEvent(map_event, expanded_actions)

    assert not event.tick(2.0)
    assert event.elapsed_time == 2.0

    assert event.tick(2.0)
    assert not event.is_cancelled()

    assert not event.tick(5.0)
    assert event.is_cancelled()


def test_tick_active_window(expanded_actions):
    map_event = Mock(id=1, priority=5, delay=3.0, timeout=8.0)
    event = RunningEvent(map_event, expanded_actions)

    assert not event.tick(2.0)
    assert not event.is_cancelled()

    assert event.tick(2.0)
    assert not event.is_cancelled()

    assert event.tick(3.0)
    assert not event.is_cancelled()

    assert not event.tick(2.0)
    assert event.is_cancelled()


def test_tick_active_window_with_context_flag(expanded_actions):
    map_event = Mock(id=1, priority=5, delay=3.0, timeout=8.0)
    event = RunningEvent(map_event, expanded_actions)

    assert not event.tick(2.0)
    assert "window_triggered" not in event.context

    ready = event.tick(2.0)
    assert ready
    if ready and not event.context.get("window_triggered"):
        event.context["window_triggered"] = True

    assert event.context["window_triggered"]

    ready = event.tick(2.0)
    assert ready
    assert event.context["window_triggered"]

    ready = event.tick(3.0)
    assert not ready
    assert event.is_cancelled()


def test_running_event_delay_prevents_start(simple_event):
    simple_event.delay = 2.0
    simple_event.timeout = None
    running = RunningEvent(simple_event, [Mock()])
    session = Mock()
    action_manager = Mock()
    assert running.process(session, action_manager, 1.0) is True
    assert running.current_action is None
    assert running.state == EventState.WAITING


def test_running_event_timeout_cancels(simple_event):
    simple_event.delay = None
    simple_event.timeout = 1.0
    running = RunningEvent(simple_event, [Mock()])
    session = Mock()
    action_manager = Mock()
    action_manager.get_action.return_value = Mock(done=False, cancelled=False)
    assert running.process(session, action_manager, 0.6) is True
    assert running.process(session, action_manager, 0.6) is False
    assert running.state == EventState.CANCELLED


def test_running_event_instant_action(simple_event):
    simple_event.delay = None
    simple_event.timeout = None
    running = RunningEvent(simple_event, [Mock()])
    session = Mock()
    action_manager = Mock()
    instant = Mock(done=True, cancelled=False)
    action_manager.get_action.return_value = instant
    assert running.process(session, action_manager, 0.1) is False
    assert running.action_index == 1
    assert running.state == EventState.COMPLETED


def test_running_event_long_running(simple_event):
    simple_event.delay = None
    simple_event.timeout = None
    running = RunningEvent(simple_event, [Mock()])
    session = Mock()
    action_manager = Mock()
    long_action = Mock(done=False, cancelled=False)
    action_manager.get_action.return_value = long_action
    assert running.process(session, action_manager, 0.1) is True
    assert running.current_action is long_action
    assert running.state == EventState.WAITING


def test_running_event_invalid_action(simple_event):
    simple_event.delay = None
    simple_event.timeout = None
    running = RunningEvent(simple_event, [Mock()])
    session = Mock()
    action_manager = Mock()
    action_manager.get_action.return_value = None
    assert running.process(session, action_manager, 0.1) is False
    assert running.state == EventState.CANCELLED


def test_running_event_cancel_mid_update(simple_event):
    simple_event.delay = None
    simple_event.timeout = None
    running = RunningEvent(simple_event, [Mock()])
    session = Mock()
    action_manager = Mock()
    action = Mock(done=False, cancelled=False)
    action_manager.get_action.return_value = action
    assert running.process(session, action_manager, 0.1) is True
    action.cancelled = True
    assert running.process(session, action_manager, 0.1) is False
    assert running.state == EventState.COMPLETED


def test_running_event_mixed_actions(simple_event):
    simple_event.delay = None
    simple_event.timeout = None
    rule1 = Mock()
    rule2 = Mock()
    running = RunningEvent(simple_event, [rule1, rule2])
    session = Mock()
    action_manager = Mock()
    long_action = Mock(done=False, cancelled=False)
    instant_action = Mock(done=True, cancelled=False)
    action_manager.get_action.side_effect = [long_action, instant_action]
    assert running.process(session, action_manager, 0.1) is True
    assert running.current_action is long_action
    long_action.done = True
    assert running.process(session, action_manager, 0.1) is False
    assert running.state == EventState.COMPLETED
    assert running.action_index == 2


def test_running_event_action_update_exception(simple_event):
    simple_event.delay = None
    simple_event.timeout = None
    running = RunningEvent(simple_event, [Mock()])
    session = Mock()
    action_manager = Mock()
    bad_action = Mock(done=False, cancelled=False)
    bad_action.update.side_effect = RuntimeError("boom")
    action_manager.get_action.return_value = bad_action
    with pytest.raises(RuntimeError):
        running.process(session, action_manager, 0.1)


def test_running_event_invalid_action_type(simple_event):
    simple_event.delay = None
    simple_event.timeout = None
    running = RunningEvent(simple_event, [Mock()])
    session = Mock()
    action_manager = Mock()
    action_manager.get_action.return_value = None
    assert running.process(session, action_manager, 0.1) is False
    assert running.state == EventState.CANCELLED


def test_running_event_action_clears_itself(simple_event):
    simple_event.delay = None
    simple_event.timeout = None
    running = RunningEvent(simple_event, [Mock()])
    session = Mock()
    action_manager = Mock()

    class WeirdAction:
        done = False
        cancelled = False

        def on_start(self, session):
            pass

        def update(self, session, dt):
            running.current_action = None

    action_manager.get_action.return_value = WeirdAction()
    assert running.process(session, action_manager, 0.1) is False
    assert running.state == EventState.CANCELLED


def test_running_event_reset(simple_event):
    simple_event.delay = None
    simple_event.timeout = None
    running = RunningEvent(simple_event, [Mock(), Mock()])
    session = Mock()
    action_manager = Mock()
    action = Mock(done=False, cancelled=False)
    action_manager.get_action.return_value = action
    running.process(session, action_manager, 0.1)
    assert running.current_action is action
    assert running.action_index == 0
    assert running.elapsed_time > 0
    assert running.state == EventState.WAITING
    running.reset()
    assert running.action_index == 0
    assert running.current_action is None
    assert running.elapsed_time == 0.0
    assert running.state == EventState.WAITING
    assert running.context == {}


def test_advance_does_not_complete_prematurely(simple_event, expanded_actions):
    event = RunningEvent(simple_event, expanded_actions)
    event.running()
    event.advance()
    event.advance()
    event.advance()
    assert event.state == EventState.RUNNING
    assert event.action_index == 3


def test_get_next_action_returns_none_when_index_exhausted(
    simple_event, expanded_actions
):
    event = RunningEvent(simple_event, expanded_actions)
    event.action_index = len(expanded_actions)
    assert event.get_next_action() is None
    assert event.state != EventState.COMPLETED


def test_step_returns_false_when_completed(simple_event, expanded_actions):
    event = RunningEvent(simple_event, expanded_actions)
    event.complete()
    result = event.step(Mock(), Mock(), 0.1)
    assert result is False


def test_step_returns_false_when_cancelled(simple_event, expanded_actions):
    event = RunningEvent(simple_event, expanded_actions)
    event.cancel()
    result = event.step(Mock(), Mock(), 0.1)
    assert result is False


def test_step_delegates_to_process_when_running(simple_event):
    simple_event.delay = None
    simple_event.timeout = None
    running = RunningEvent(simple_event, [Mock()])
    session = Mock()
    action_manager = Mock()
    long_action = Mock(done=False, cancelled=False)
    action_manager.get_action.return_value = long_action
    running.running()
    result = running.step(session, action_manager, 0.1)
    assert result is True


def test_is_alive(simple_event, expanded_actions):
    event = RunningEvent(simple_event, expanded_actions)
    assert event.is_alive()
    event.complete()
    assert not event.is_alive()


def test_is_alive_false_when_cancelled(simple_event, expanded_actions):
    event = RunningEvent(simple_event, expanded_actions)
    event.cancel()
    assert not event.is_alive()


def test_action_budget_yields_instead_of_spinning(simple_event):
    simple_event.delay = None
    simple_event.timeout = None

    n = 5
    rules = [Mock() for _ in range(n)]
    running = RunningEvent(simple_event, rules)
    session = Mock()
    action_manager = Mock()

    def self_cancelling(*args, **kwargs):
        return Mock(done=False, cancelled=True)

    action_manager.get_action.side_effect = self_cancelling

    result = running.process(session, action_manager, 0.1)

    assert result is False
    assert running.state == EventState.COMPLETED
    assert running.action_index == n


def test_cancel_mid_sequence_continues_to_next_action(simple_event):
    simple_event.delay = None
    simple_event.timeout = None
    rule1 = Mock()
    rule2 = Mock()
    running = RunningEvent(simple_event, [rule1, rule2])
    session = Mock()
    action_manager = Mock()

    cancelled_action = Mock(done=False, cancelled=False)
    long_action = Mock(done=False, cancelled=False)
    action_manager.get_action.side_effect = [cancelled_action, long_action]

    result = running.process(session, action_manager, 0.1)
    assert result is True
    assert running.current_action is cancelled_action

    cancelled_action.cancelled = True

    result = running.process(session, action_manager, 0.1)
    assert result is True
    assert running.current_action is long_action
    assert running.state != EventState.COMPLETED


def test_repr(simple_event, expanded_actions):
    event = RunningEvent(simple_event, expanded_actions)
    event.running()
    r = repr(event)
    assert "RunningEvent" in r
    assert str(simple_event.id) in r
    assert "RUNNING" in r
