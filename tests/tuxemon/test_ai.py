# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import MagicMock

from tuxemon.ai import (
    OpponentEvaluator,
    TrainerAIDecisionStrategy,
    WildAIDecisionStrategy,
)


class TestRecharging(unittest.TestCase):
    def test_recharging(self):
        mock_technique = MagicMock()
        mock_technique.next_use = 0
        global recharging
        recharging = MagicMock(side_effect=lambda move: move.next_use == 0)
        self.assertTrue(
            recharging(mock_technique), "The technique should be recharging."
        )

    def test_not_recharging(self):
        mock_technique = MagicMock()
        mock_technique.next_use = 1
        global recharging
        recharging = MagicMock(side_effect=lambda move: move.next_use == 0)
        self.assertFalse(
            recharging(mock_technique),
            "The technique should not be recharging.",
        )


class TestOpponentEvaluator(unittest.TestCase):
    def test_evaluate(self):
        mock_opponent = MagicMock()
        mock_opponent.current_hp = 50
        mock_opponent.hp = 100
        evaluator = OpponentEvaluator(opponents=[mock_opponent])
        score = evaluator.evaluate(mock_opponent)
        self.assertEqual(score, 0.5)

    def test_get_best_target(self):
        mock_opponent_1 = MagicMock()
        mock_opponent_1.current_hp = 20
        mock_opponent_1.hp = 100
        mock_opponent_2 = MagicMock()
        mock_opponent_2.current_hp = 80
        mock_opponent_2.hp = 100
        opponents = [mock_opponent_1, mock_opponent_2]
        evaluator = OpponentEvaluator(opponents=opponents)
        best_target = evaluator.get_best_target()
        self.assertEqual(best_target, mock_opponent_2)


class TestTrainerAIDecisionStrategy(unittest.TestCase):
    def test_make_decision_use_potion(self):
        mock_ai = MagicMock()
        mock_ai.character.items = [MagicMock(category="potion")]
        mock_ai.need_potion.return_value = True

        mock_evaluator = MagicMock()
        mock_tracker = MagicMock()

        strategy = TrainerAIDecisionStrategy(mock_evaluator, mock_tracker)
        strategy.make_decision(mock_ai)

        mock_ai.action_item.assert_called_once_with(mock_ai.character.items[0])
        mock_evaluator.get_best_target.assert_not_called()
        mock_tracker.get_valid_moves.assert_not_called()

    def test_make_decision_select_move(self):
        mock_ai = MagicMock()
        mock_ai.character.items = []
        mock_ai.need_potion.return_value = False

        mock_evaluator = MagicMock()
        mock_evaluator.get_best_target.return_value = MagicMock()

        mock_tracker = MagicMock()
        mock_tracker.get_valid_moves.return_value = [
            (MagicMock(), MagicMock())
        ]

        strategy = TrainerAIDecisionStrategy(mock_evaluator, mock_tracker)
        strategy.make_decision(mock_ai)

        mock_ai.action_item.assert_not_called()
        mock_tracker.get_valid_moves.assert_called_once_with(mock_ai.opponents)
        mock_ai.action_tech.assert_called_once()


class TestWildAIDecisionStrategy(unittest.TestCase):
    def test_make_decision(self):
        mock_ai = MagicMock()

        mock_evaluator = MagicMock()
        mock_evaluator.get_best_target.return_value = MagicMock()

        mock_tracker = MagicMock()
        mock_tracker.get_valid_moves.return_value = [
            (MagicMock(), MagicMock())
        ]

        strategy = WildAIDecisionStrategy(mock_evaluator, mock_tracker)
        strategy.make_decision(mock_ai)

        mock_ai.action_tech.assert_called_once()
