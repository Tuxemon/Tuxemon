# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import MagicMock

from tuxemon.ai import (
    AIConfigLoader,
    AIItems,
    ItemEntry,
    OpponentEvaluator,
    TrainerAIDecisionStrategy,
    WildAIDecisionStrategy,
)


class TestRecharging(unittest.TestCase):
    def test_recharging(self):
        mock_technique = MagicMock(next_use=0)
        global recharging
        recharging = MagicMock(side_effect=lambda move: move.next_use == 0)
        self.assertTrue(
            recharging(mock_technique), "The technique should be recharging."
        )

    def test_not_recharging(self):
        mock_technique = MagicMock(next_use=1)
        global recharging
        recharging = MagicMock(side_effect=lambda move: move.next_use == 0)
        self.assertFalse(
            recharging(mock_technique),
            "The technique should not be recharging.",
        )


class TestOpponentEvaluator(unittest.TestCase):
    def setUp(self):
        self.mock_combat = MagicMock()
        self.mock_user = MagicMock(
            slug="rockitten", current_hp=50, hp=100, level=10
        )

    def test_evaluate(self):
        mock_opponent = MagicMock(current_hp=50, hp=100, level=10)

        evaluator = OpponentEvaluator(
            combat=self.mock_combat,
            user=self.mock_user,
            opponents=[mock_opponent],
        )
        evaluator.evaluate = MagicMock(
            side_effect=lambda opponent: opponent.current_hp / opponent.hp
        )

        score = evaluator.evaluate(mock_opponent)
        self.assertEqual(score, 0.5)

    def test_get_best_target(self):
        mock_opponent_1 = MagicMock(current_hp=20, hp=100, level=10)
        mock_opponent_2 = MagicMock(current_hp=80, hp=100, level=10)

        evaluator = OpponentEvaluator(
            combat=self.mock_combat,
            user=self.mock_user,
            opponents=[mock_opponent_1, mock_opponent_2],
        )
        evaluator.evaluate = MagicMock(
            side_effect=lambda opponent: opponent.current_hp / opponent.hp
        )

        best_target = evaluator.get_best_target()
        self.assertEqual(best_target, mock_opponent_2)


class TestTrainerAIDecisionStrategy(unittest.TestCase):
    def setUp(self):
        self.mock_ai = MagicMock()
        self.mock_ai.character.items = []
        self.mock_evaluator = MagicMock()
        self.mock_tracker = MagicMock()

    def test_make_decision_use_potion(self):
        mock_item = MagicMock(slug="potion")
        self.mock_ai.character.items = [mock_item]
        AIConfigLoader.get_ai_items = MagicMock(
            return_value=AIItems(
                items={"potion": ItemEntry(hp_range=(0.2, 0.8))}
            )
        )
        self.mock_ai.monster.current_hp = 40
        self.mock_ai.monster.hp = 100

        strategy = TrainerAIDecisionStrategy(
            self.mock_evaluator, self.mock_tracker
        )
        strategy.make_decision(self.mock_ai)

        self.mock_ai.action_item.assert_called_once_with(mock_item)

    def test_make_decision_select_move(self):
        self.mock_tracker.get_valid_moves.return_value = [
            (MagicMock(), MagicMock())
        ]
        self.mock_evaluator.get_best_target.return_value = MagicMock()

        self.mock_tracker.evaluate_technique.return_value = 10.0

        strategy = TrainerAIDecisionStrategy(
            self.mock_evaluator, self.mock_tracker
        )
        strategy.make_decision(self.mock_ai)

        self.mock_tracker.get_valid_moves.assert_called_once_with(
            self.mock_ai.opponents
        )
        self.mock_ai.action_tech.assert_called_once()


class TestWildAIDecisionStrategy(unittest.TestCase):
    def setUp(self):
        self.mock_ai = MagicMock()
        self.mock_evaluator = MagicMock()
        self.mock_tracker = MagicMock()

    def test_make_decision(self):
        self.mock_tracker.get_valid_moves.return_value = [
            (MagicMock(), MagicMock())
        ]
        self.mock_tracker.evaluate_technique.return_value = 5.0
        self.mock_evaluator.get_best_target.return_value = MagicMock()

        strategy = WildAIDecisionStrategy(
            self.mock_evaluator, self.mock_tracker
        )
        strategy.make_decision(self.mock_ai)

        self.mock_ai.action_tech.assert_called_once()
