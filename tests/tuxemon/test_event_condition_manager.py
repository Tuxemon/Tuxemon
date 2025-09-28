# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import MagicMock, patch

from tuxemon.event import MapCondition
from tuxemon.event.eventcondition import ConditionManager, EventCondition
from tuxemon.event.running import ConditionEvaluator


class TestConditionManager(unittest.TestCase):
    def setUp(self):
        patcher = patch("tuxemon.plugin.load_plugins")
        self.mock_load_plugins = patcher.start()
        self.addCleanup(patcher.stop)

        # Create mock condition classes
        self.mock_condition_class = MagicMock()
        self.mock_load_plugins.return_value = {
            "char_at": self.mock_condition_class
        }

        self.condition_manager = ConditionManager()

    def test_get_condition_found(self):
        mock_cond_data = MagicMock(spec=MapCondition)
        mock_cond_data.type = "char_at"
        mock_cond_data.operator = "is"

        condition = self.condition_manager.get_condition(mock_cond_data)
        self.assertIsNotNone(condition)
        self.assertEqual(condition.is_expected, True)

    def test_get_condition_not_found(self):
        mock_cond_data = MagicMock(spec=MapCondition)
        mock_cond_data.type = "nonexistent"
        mock_cond_data.operator = "is"

        condition = self.condition_manager.get_condition(mock_cond_data)
        self.assertIsNone(condition)

    def test_get_condition_with_parameters(self):
        mock_cond_data = MagicMock()
        mock_cond_data.type = "char_at"
        mock_cond_data.operator = "is"
        mock_cond_data.parameters = ["hero", 0, "H"]

        # Simulate condition class accepting parameters
        self.mock_condition_class.return_value = MagicMock()
        condition = self.condition_manager.get_condition(mock_cond_data)
        self.assertIsNotNone(condition)
        self.assertEqual(condition.is_expected, True)

    def test_get_conditions_are_event_conditions(self):
        conditions = self.condition_manager.get_conditions()
        for cond_class in conditions:
            self.assertTrue(issubclass(cond_class, EventCondition))


class TestConditionEvaluator(unittest.TestCase):
    def setUp(self):
        self.mock_session = MagicMock()
        self.mock_condition = MagicMock()
        self.mock_condition.test.return_value = True
        self.mock_condition.is_expected = True

        self.mock_condition_manager = MagicMock()
        self.mock_condition_manager.get_condition.return_value = (
            self.mock_condition
        )

        self.evaluator = ConditionEvaluator(
            session=self.mock_session,
            condition_manager=self.mock_condition_manager,
        )

    def test_evaluate_condition_met(self):
        mock_map_condition = MagicMock()
        result = self.evaluator.evaluate(mock_map_condition)
        self.assertTrue(result)

    def test_evaluate_condition_failed(self):
        self.mock_condition.test.return_value = False
        result = self.evaluator.evaluate(MagicMock())
        self.assertFalse(result)

    def test_evaluate_condition_not_found(self):
        self.mock_condition_manager.get_condition.return_value = None
        with self.assertRaises(ValueError):
            self.evaluator.evaluate(MagicMock())
