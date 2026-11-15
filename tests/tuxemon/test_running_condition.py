# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock

import pytest

from tuxemon.db import BoundingBox, Operator, SpatialCondition
from tuxemon.event.eventcondition import ConditionManager
from tuxemon.event.running import (
    ConditionEvaluator,
    ConditionState,
    RunningCondition,
)
from tuxemon.session import Session


@pytest.fixture
def mock_condition():
    cond = MagicMock()
    cond.name = "TestCondition"
    cond.test.return_value = True
    cond.is_expected = True
    return cond


@pytest.fixture
def mock_condition_manager(mock_condition):
    mgr = MagicMock(spec=ConditionManager)
    mgr.get_condition.return_value = mock_condition
    return mgr


@pytest.fixture
def mock_session():
    return MagicMock(spec=Session)


@pytest.fixture
def spatial_condition():
    box = BoundingBox(x=0, y=0, width=1, height=1)
    return SpatialCondition(
        type="test_type",
        parameters=[],
        box=box,
        operator=Operator.IS,
        name="TestCondition",
    )


@pytest.fixture
def evaluator(mock_session, mock_condition_manager):
    return ConditionEvaluator(
        session=mock_session,
        condition_manager=mock_condition_manager,
    )


@pytest.fixture
def running_condition(spatial_condition, evaluator):
    return RunningCondition(spatial_condition, evaluator)


class TestConditionState:
    def test_has_met(self):
        assert hasattr(ConditionState, "MET")

    def test_has_failed(self):
        assert hasattr(ConditionState, "FAILED")

    def test_has_cancelled(self):
        assert hasattr(ConditionState, "CANCELLED")

    def test_no_waiting(self):
        assert not hasattr(ConditionState, "WAITING")

    def test_no_checking(self):
        assert not hasattr(ConditionState, "CHECKING")


class TestRunningConditionInit:
    def test_initial_state_is_failed(self, running_condition):
        assert running_condition.state == ConditionState.FAILED

    def test_initial_result_is_none(self, running_condition):
        assert running_condition.result is None

    def test_no_start_check_method(self, running_condition):
        assert not hasattr(running_condition, "start_check")


class TestRunningConditionCheck:
    def test_check_condition_met(self, running_condition):
        result = running_condition.check()
        assert result is True
        assert running_condition.is_met()
        assert running_condition.result is True

    def test_check_condition_failed(self, running_condition, mock_condition):
        mock_condition.test.return_value = False
        result = running_condition.check()
        assert result is False
        assert running_condition.is_failed()
        assert running_condition.result is False

    def test_check_is_expected_false(self, running_condition, mock_condition):
        mock_condition.test.return_value = False
        mock_condition.is_expected = False
        result = running_condition.check()
        assert result is True
        assert running_condition.is_met()

    def test_check_condition_type_not_found(
        self, running_condition, mock_condition_manager
    ):
        mock_condition_manager.get_condition.return_value = None
        result = running_condition.check()
        assert result is False
        assert running_condition.is_failed()
        assert running_condition.result is False

    def test_check_condition_exception(
        self, running_condition, mock_condition, caplog
    ):
        mock_condition.test.side_effect = Exception("test error")
        result = running_condition.check()
        assert result is False
        assert running_condition.is_failed()
        assert running_condition.result is False
        assert "error checking condition" in caplog.text.lower()

    def test_check_cancelled_returns_false_immediately(
        self, running_condition
    ):
        running_condition.cancel()
        result = running_condition.check()
        assert result is False
        assert running_condition.is_cancelled()
        assert running_condition.result is False

    def test_check_cancelled_does_not_call_evaluator(
        self, running_condition, mock_condition_manager
    ):
        running_condition.cancel()
        running_condition.check()
        mock_condition_manager.get_condition.assert_not_called()

    def test_check_sets_result_on_success(self, running_condition):
        running_condition.check()
        assert running_condition.result is True

    def test_check_sets_result_on_failure(
        self, running_condition, mock_condition
    ):
        mock_condition.test.return_value = False
        running_condition.check()
        assert running_condition.result is False


class TestRunningConditionCancel:
    def test_cancel_sets_state(self, running_condition):
        running_condition.cancel()
        assert running_condition.state == ConditionState.CANCELLED

    def test_is_cancelled_true_after_cancel(self, running_condition):
        running_condition.cancel()
        assert running_condition.is_cancelled()

    def test_cancel_after_met_overrides_state(self, running_condition):
        running_condition.check()
        assert running_condition.is_met()
        running_condition.cancel()
        assert running_condition.is_cancelled()


class TestRunningConditionFlags:
    def test_is_met(self, running_condition):
        running_condition.state = ConditionState.MET
        assert running_condition.is_met()
        assert not running_condition.is_failed()
        assert not running_condition.is_cancelled()

    def test_is_failed(self, running_condition):
        running_condition.state = ConditionState.FAILED
        assert running_condition.is_failed()
        assert not running_condition.is_met()
        assert not running_condition.is_cancelled()

    def test_is_cancelled(self, running_condition):
        running_condition.state = ConditionState.CANCELLED
        assert running_condition.is_cancelled()
        assert not running_condition.is_met()
        assert not running_condition.is_failed()


class TestConditionEvaluator:
    def test_evaluate_passes_when_expected(
        self, evaluator, spatial_condition, mock_condition
    ):
        mock_condition.test.return_value = True
        mock_condition.is_expected = True
        assert evaluator.evaluate(spatial_condition) is True

    def test_evaluate_fails_when_unexpected(
        self, evaluator, spatial_condition, mock_condition
    ):
        mock_condition.test.return_value = True
        mock_condition.is_expected = False
        assert evaluator.evaluate(spatial_condition) is False

    def test_evaluate_raises_when_condition_not_found(
        self, evaluator, spatial_condition, mock_condition_manager
    ):
        mock_condition_manager.get_condition.return_value = None
        with pytest.raises(ValueError, match="not found"):
            evaluator.evaluate(spatial_condition)

    def test_evaluate_clears_condition_box_on_success(
        self, evaluator, spatial_condition, mock_session
    ):
        evaluator.evaluate(spatial_condition)
        assert mock_session.current_condition_box is None

    def test_evaluate_clears_condition_box_on_exception(
        self, evaluator, spatial_condition, mock_condition, mock_session
    ):
        mock_condition.test.side_effect = RuntimeError("boom")
        with pytest.raises(RuntimeError):
            evaluator.evaluate(spatial_condition)
        assert mock_session.current_condition_box is None
