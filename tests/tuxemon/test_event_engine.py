# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import logging
from unittest.mock import MagicMock, patch

import pytest

from tuxemon.client import LocalPygameClient
from tuxemon.db import BoundingBox, EventObject
from tuxemon.event.eventaction import ActionManager
from tuxemon.event.eventbehavior import BehaviorManager
from tuxemon.event.eventengine import EventEngine
from tuxemon.event.running import ConditionEvaluator, EventState
from tuxemon.map.manager import MapManager
from tuxemon.session import Session, local_session


@pytest.fixture
def event_engine():
    box = BoundingBox(x=0, y=0, width=1, height=1)
    action = MagicMock(spec=ActionManager)
    evaluator = MagicMock(spec=ConditionEvaluator)
    behavior = MagicMock(spec=BehaviorManager)
    eng = EventEngine(local_session, action, evaluator, behavior)
    eng._test_box = box
    return eng


def make_event(event_id, box, behavs=None):
    return EventObject(
        id=event_id,
        name="",
        priority=0,
        box=box,
        conds=[],
        acts=[],
        behavs=behavs or [],
    )


def _mock_session(event_engine, inits=None):
    event_engine.session = MagicMock(spec=Session)
    event_engine.session.client = MagicMock(spec=LocalPygameClient)
    event_engine.session.client.map_manager = MagicMock(spec=MapManager)
    event_engine.session.client.map_manager.inits = inits or []


class TestInit:
    def test_initial_state(self, event_engine):
        assert event_engine.current_map is None
        assert event_engine.running_events == {}
        assert event_engine.partial_events == []
        assert event_engine._behavior_cache == {}
        assert event_engine.global_events == []
        assert event_engine.triggered_global_events == set()


class TestReset:
    def test_clears_running_events_and_map(self, event_engine):
        event_engine.running_events = {1: "event1", 2: "event2"}
        event_engine.current_map = "map1"
        event_engine.reset()
        assert event_engine.current_map is None
        assert event_engine.running_events == {}

    def test_clears_behavior_cache(self, event_engine):
        event_engine._behavior_cache = {1: ([], [])}
        event_engine.reset()
        assert event_engine._behavior_cache == {}

    def test_clears_triggered_global_events(self, event_engine):
        event_engine.triggered_global_events = {1, 2, 3}
        event_engine.reset()
        assert event_engine.triggered_global_events == set()


class TestStartEvent:
    def test_event_added_to_running(self, event_engine):
        event = make_event(1, event_engine._test_box)
        _mock_session(event_engine)
        event_engine.start_event(event)
        assert 1 in event_engine.running_events

    def test_duplicate_start_ignored(self, event_engine):
        event = make_event(1, event_engine._test_box)
        _mock_session(event_engine)
        event_engine.start_event(event)
        event_engine.start_event(event)
        assert len(event_engine.running_events) == 1

    def test_uses_expand_behavior_not_split_functions(self, event_engine):
        event = make_event(1, event_engine._test_box)
        _mock_session(event_engine)

        with patch("tuxemon.event.eventengine.expand_behavior") as expand:
            expand.return_value = ([], [])
            event_engine.start_event(event)
            expand.assert_called_once_with(
                event, event_engine.behavior_manager
            )

    def test_behavior_expansion_cached(self, event_engine):
        event = make_event(1, event_engine._test_box)
        _mock_session(event_engine)

        with patch("tuxemon.event.eventengine.expand_behavior") as expand:
            expand.return_value = ([], [])
            event_engine._get_behavior_expansion(event)
            event_engine._get_behavior_expansion(event)
            assert expand.call_count == 1

    def test_behavior_cache_cleared_each_update(self, event_engine):
        event_engine.check_global_conditions = MagicMock()
        event_engine.check_conditions = MagicMock()
        event_engine.update_running_events = MagicMock()
        event_engine._behavior_cache = {99: ([], [])}
        event_engine.update(0.1)
        assert event_engine._behavior_cache == {}


class TestGlobalEvents:
    def test_register_prevents_duplicates(self, event_engine):
        event = make_event(99, event_engine._test_box)
        event_engine.global_events = [event]
        result = event_engine.register_global_event(event)
        assert result is False
        assert len(event_engine.global_events) == 1

    def test_register_sorts_by_priority(self, event_engine):
        low = make_event(1, event_engine._test_box)
        low.priority = 0
        high = make_event(2, event_engine._test_box)
        high.priority = 10
        event_engine.register_global_event(low)
        event_engine.register_global_event(high)
        assert event_engine.global_events[0].id == 2

    def test_unregister_removes_event(self, event_engine):
        event = make_event(77, event_engine._test_box)
        event_engine.global_events = [event]
        event_engine.triggered_global_events = {77}
        result = event_engine.unregister_global_event(77)
        assert result is True
        assert event not in event_engine.global_events
        assert 77 not in event_engine.triggered_global_events

    def test_unregister_missing_returns_false(self, event_engine):
        result = event_engine.unregister_global_event(999)
        assert result is False

    def test_global_event_triggers_only_once(self, event_engine):
        event = make_event(1, event_engine._test_box)
        event.conds = [MagicMock()]
        event.conds[0].check.return_value = True
        event_engine.global_events = [event]
        event_engine.start_event = MagicMock()
        event_engine.check_global_conditions()
        event_engine.start_event.assert_called_once_with(event)
        event_engine.start_event.reset_mock()
        event_engine.check_global_conditions()
        event_engine.start_event.assert_not_called()

    def test_cancel_event_clears_triggered_global(self, event_engine):
        running = MagicMock()
        event_engine.running_events = {1: running}
        event_engine.triggered_global_events = {1}
        event_engine.cancel_event(1)
        assert 1 not in event_engine.triggered_global_events

    def test_cancel_all_events_clears_triggered_globals(self, event_engine):
        r1, r2 = MagicMock(), MagicMock()
        event_engine.running_events = {1: r1, 2: r2}
        event_engine.triggered_global_events = {1, 2}
        event_engine.cancel_all_events()
        assert event_engine.triggered_global_events == set()


class TestConditionEvaluation:
    def test_event_starts_when_conditions_met(self, event_engine):
        event = make_event(1, event_engine._test_box)
        cond = MagicMock()
        cond.check.return_value = True
        event.conds = [cond]
        event_engine.evaluator = MagicMock()
        event_engine.start_event = MagicMock()
        event_engine._evaluate_and_queue_event(event)
        event_engine.start_event.assert_called_once_with(event)

    def test_event_does_not_start_when_conditions_fail(self, event_engine):
        event = make_event(1, event_engine._test_box)
        cond = MagicMock()
        event.conds = [cond]
        event_engine.evaluator.evaluate.return_value = False
        event_engine.start_event = MagicMock()
        event_engine._evaluate_and_queue_event(event)
        event_engine.start_event.assert_not_called()

    def test_event_with_no_conditions_not_started(self, event_engine):
        event = make_event(1, event_engine._test_box)
        event_engine.start_event = MagicMock()
        event_engine._evaluate_and_queue_event(event)
        event_engine.start_event.assert_not_called()


class TestUpdateRunningEvents:
    def test_completed_events_removed(self, event_engine):
        running = MagicMock()
        running.is_running.return_value = True
        running.step.return_value = False
        running.state = EventState.COMPLETED
        event_engine.running_events = {1: running}
        event_engine.update_running_events(0.1)
        assert event_engine.running_events == {}

    def test_cancelled_events_removed(self, event_engine):
        running = MagicMock()
        running.is_running.return_value = True
        running.step.return_value = False
        running.state = EventState.CANCELLED
        event_engine.running_events = {1: running}
        event_engine.update_running_events(0.1)
        assert event_engine.running_events == {}

    def test_active_events_kept(self, event_engine):
        running = MagicMock()
        running.is_running.return_value = True
        running.step.return_value = True
        running.state = EventState.RUNNING
        event_engine.running_events = {1: running}
        event_engine.update_running_events(0.1)
        assert 1 in event_engine.running_events

    def test_map_change_aborts_processing(self, event_engine):
        running = MagicMock()
        running.is_running.return_value = True

        def change_map(*args, **kwargs):
            event_engine.current_map = "mapB"
            return True

        running.step.side_effect = change_map
        event_engine.running_events = {1: running}
        event_engine.current_map = "mapA"
        event_engine.update_running_events(0.1)
        running.step.assert_called_once()

    def test_not_running_events_skipped(self, event_engine):
        running = MagicMock()
        running.is_running.return_value = False
        event_engine.running_events = {1: running}
        event_engine.update_running_events(0.1)
        running.step.assert_not_called()


class TestCancelEvents:
    def test_cancel_event_calls_cancel(self, event_engine):
        running = MagicMock()
        event_engine.running_events = {1: running}
        event_engine.cancel_event(1)
        running.cancel.assert_called_once()

    def test_cancel_event_missing_id_safe(self, event_engine):
        event_engine.cancel_event(999)

    def test_cancel_all_events(self, event_engine):
        r1, r2 = MagicMock(), MagicMock()
        event_engine.running_events = {1: r1, 2: r2}
        event_engine.cancel_all_events()
        r1.cancel.assert_called_once()
        r2.cancel.assert_called_once()


class TestSuspendResume:
    def test_suspended_engine_skips_update(self, event_engine):
        event_engine.suspend()
        event_engine.check_conditions = MagicMock()
        event_engine.update(0.1)
        event_engine.check_conditions.assert_not_called()

    def test_resumed_engine_processes_update(self, event_engine):
        event_engine.suspend()
        event_engine.resume()
        event_engine.check_conditions = MagicMock()
        event_engine.check_global_conditions = MagicMock()
        event_engine.update_running_events = MagicMock()
        event_engine.update(0.1)
        event_engine.check_conditions.assert_called_once()

    def test_double_suspend_does_not_log_twice(self, event_engine, caplog):
        with caplog.at_level(logging.INFO, logger="tuxemon.event.eventengine"):
            event_engine.suspend()
            event_engine.suspend()
        assert caplog.text.count("suspended") == 1

    def test_double_resume_does_not_log_twice(self, event_engine, caplog):
        with caplog.at_level(logging.INFO, logger="tuxemon.event.eventengine"):
            event_engine.suspend()
            event_engine.resume()
            event_engine.resume()
        assert caplog.text.count("resumed") == 1
