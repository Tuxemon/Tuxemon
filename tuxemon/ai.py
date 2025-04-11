# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from tuxemon.combat import pre_checking, recharging
from tuxemon.db import ItemCategory
from tuxemon.technique.technique import Technique

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.monster import Monster
    from tuxemon.npc import NPC
    from tuxemon.states.combat.combat import CombatState


class TechniqueTracker:
    def __init__(self, moves: list[Technique]):
        self.moves = moves

    def get_valid_moves(
        self, opponents: list[Monster]
    ) -> list[tuple[Technique, Monster]]:
        """Returns valid techniques and their corresponding opponents."""
        return [
            (mov, opponent)
            for mov in self.moves
            if not recharging(mov)
            for opponent in opponents
            if mov.validate_monster(opponent)
        ]


class OpponentEvaluator:
    def __init__(self, opponents: list[Monster]):
        self.opponents = opponents

    def evaluate(self, opponent: Monster) -> float:
        """
        Scores opponents based on their current health, status effects, and power level.
        Higher scores indicate better targets.
        """
        score = opponent.current_hp / opponent.hp
        return score

    def get_best_target(self) -> Monster:
        """Returns the opponent with the highest evaluation score."""
        return max(self.opponents, key=self.evaluate)


class AIDecisionStrategy(ABC):
    def __init__(
        self, evaluator: OpponentEvaluator, tracker: TechniqueTracker
    ):
        self.evaluator = evaluator
        self.tracker = tracker

    @abstractmethod
    def make_decision(self, ai: AI) -> None:
        pass

    @abstractmethod
    def select_move(
        self, ai: AI, target: Monster
    ) -> tuple[Technique, Monster]:
        pass


class TrainerAIDecisionStrategy(AIDecisionStrategy):
    def make_decision(self, ai: AI) -> None:
        """Trainer battle decision-making"""
        if len(ai.character.items) > 0:
            for itm in ai.character.items:
                if itm.category == ItemCategory.potion:
                    if ai.need_potion():
                        ai.action_item(itm)
                        return

        target = self.evaluator.get_best_target()
        technique, target = self.select_move(ai, target)
        ai.action_tech(technique, target)

    def select_move(
        self, ai: AI, target: Monster
    ) -> tuple[Technique, Monster]:
        """Select the most effective move and target."""
        valid_actions = self.tracker.get_valid_moves(ai.opponents)

        if not valid_actions:
            skip = Technique()
            skip.load("skip")
            return skip, target

        return random.choice(valid_actions)


class WildAIDecisionStrategy(AIDecisionStrategy):
    def make_decision(self, ai: AI) -> None:
        """Wild encounter decision-making: focus on moves."""
        target = self.evaluator.get_best_target()
        technique, target = self.select_move(ai, target)
        ai.action_tech(technique, target)

    def select_move(
        self, ai: AI, target: Monster
    ) -> tuple[Technique, Monster]:
        """Select the most effective move and target."""
        valid_actions = self.tracker.get_valid_moves(ai.opponents)

        if not valid_actions:
            skip = Technique()
            skip.load("skip")
            return skip, target

        return random.choice(valid_actions)


class AI:
    def __init__(
        self, combat: CombatState, monster: Monster, character: NPC
    ) -> None:
        self.combat = combat
        self.character = character
        self.monster = monster
        self.opponents: list[Monster] = (
            combat.monsters_in_play[combat.players[1]]
            if character == combat.players[0]
            else combat.monsters_in_play[combat.players[0]]
        )

        self.evaluator = OpponentEvaluator(self.opponents)
        self.tracker = TechniqueTracker(self.monster.moves)

        self.decision_strategy = (
            TrainerAIDecisionStrategy(self.evaluator, self.tracker)
            if self.combat.is_trainer_battle
            else WildAIDecisionStrategy(self.evaluator, self.tracker)
        )

        self.decision_strategy.make_decision(self)

    def get_available_moves(self) -> list[tuple[Technique, Monster]]:
        """
        Use TechniqueTracker to get valid moves.
        """
        return self.tracker.get_valid_moves(self.opponents)

    def evaluate_best_opponent(self) -> Monster:
        """
        Use OpponentEvaluator to find the best target opponent.
        """
        return self.evaluator.get_best_target()

    def need_potion(self) -> bool:
        """
        It checks if the current_hp are less than the 15%.
        """
        return (
            self.monster.current_hp > 1
            and self.monster.current_hp <= round(self.monster.hp * 0.15)
        )

    def action_tech(self, technique: Technique, target: Monster) -> None:
        """
        Send action tech.
        """
        self.character.game_variables["action_tech"] = technique.slug
        technique = pre_checking(self.monster, technique, target, self.combat)
        self.combat.enqueue_action(self.monster, technique, target)

    def action_item(self, item: Item) -> None:
        """
        Send action item.
        """
        self.combat.enqueue_action(self.character, item, self.monster)
