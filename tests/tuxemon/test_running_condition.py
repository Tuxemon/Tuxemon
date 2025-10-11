# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import MagicMock, patch

from tuxemon.event import MapCondition
from tuxemon.event.eventcondition import ConditionManager
from tuxemon.event.running import (
    ConditionEvaluator,
    ConditionState,
    RunningCondition,
)
from tuxemon.session import Session


class TestRunningCondition(unittest.TestCase):

    def setUp(self):
        self.mock_condition = MagicMock()
        self.mock_condition.name = "TestCondition"
        self.mock_condition.test = MagicMock(return_value=True)
        self.mock_condition.is_expected = True

        self.mock_condition_manager = MagicMock(spec=ConditionManager)
        self.mock_condition_manager.get_condition.return_value = (
            self.mock_condition
        )

        self.mock_session = MagicMock(spec=Session)

        self.evaluator = ConditionEvaluator(
            session=self.mock_session,
            condition_manager=self.mock_condition_manager,
        )

        self.map_condition = MapCondition(
            type="test_type",
            parameters={},
            x=0,
            y=0,
            width=1,
            height=1,
            operator="is",
            name="TestCondition",
        )

        self.running_condition = RunningCondition(
            self.map_condition, self.evaluator
        )

    def test_initial_state(self):
        self.assertEqual(self.running_condition.state, ConditionState.WAITING)
        self.assertIsNone(self.running_condition.result)

    def test_start_check_sets_state_to_checking(self):
        self.running_condition.start_check()
        self.assertEqual(self.running_condition.state, ConditionState.CHECKING)

    def test_cancel_sets_state_to_cancelled(self):
        self.running_condition.cancel()
        self.assertTrue(self.running_condition.is_cancelled())
        self.assertEqual(
            self.running_condition.state, ConditionState.CANCELLED
        )

    def test_check_condition_met(self):
        result = self.running_condition.check()
        self.assertTrue(result)
        self.assertTrue(self.running_condition.is_met())
        self.assertEqual(self.running_condition.result, True)

    def test_check_condition_failed(self):
        self.mock_condition.test.return_value = False
        result = self.running_condition.check()
        self.assertFalse(result)
        self.assertTrue(self.running_condition.is_failed())
        self.assertEqual(self.running_condition.result, False)

    def test_check_condition_type_not_found(self):
        self.mock_condition_manager.get_condition.return_value = None
        result = self.running_condition.check()
        self.assertFalse(result)
        self.assertTrue(self.running_condition.is_failed())
        self.assertEqual(self.running_condition.result, False)

    def test_check_condition_exception(self):
        self.mock_condition.test.side_effect = Exception("Test error")
        result = self.running_condition.check()
        self.assertFalse(result)
        self.assertTrue(self.running_condition.is_failed())
        self.assertEqual(self.running_condition.result, False)

    def test_check_cancelled_condition(self):
        self.running_condition.cancel()
        result = self.running_condition.check()
        self.assertFalse(result)
        self.assertTrue(self.running_condition.is_cancelled())
        self.assertEqual(self.running_condition.result, False)

    def test_is_met_and_is_failed_and_is_cancelled_flags(self):
        self.running_condition.state = ConditionState.MET
        self.assertTrue(self.running_condition.is_met())
        self.running_condition.state = ConditionState.FAILED
        self.assertTrue(self.running_condition.is_failed())
        self.running_condition.state = ConditionState.CANCELLED
        self.assertTrue(self.running_condition.is_cancelled())
