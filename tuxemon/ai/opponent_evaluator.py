# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tuxemon.ai.ai import AIOpponent, UserMonsterEntry
    from tuxemon.monster.monster import Monster
    from tuxemon.session import Session

logger = logging.getLogger(__name__)


@dataclass
class ScoreResult:
    total: float
    breakdown: dict[str, float]


class OpponentEvaluator:
    def __init__(
        self,
        session: Session,
        user: Monster,
        opponents: list[Monster],
        ai_opponent: AIOpponent,
    ):
        self.session = session
        self.user = user
        self.opponents = opponents
        self.ai_opponent = ai_opponent

    def evaluate(self, opponent: Monster) -> float:
        """
        Scores opponents based on their current health, status effects, and power level.
        Higher scores indicate better targets.
        """
        if (
            not self.session.client.combat_session.is_trainer_battle
            or not self.session.client.combat_session.is_double
        ):
            return 1.0

        owner = self.user.get_owner()

        config = self.ai_opponent.rules.get(
            owner.slug, self.ai_opponent.rules.get("default")
        )

        if config is None:
            return 1.0

        result = calculate_score(config, self.user, opponent)
        logger.debug(
            f"Evaluation breakdown for {opponent.slug}: {result.breakdown}"
        )
        logger.debug(f"Final total score: {result.total}")
        return result.total

    def get_best_target(self) -> Monster:
        """Returns the opponent with the highest evaluation score."""
        best_target = max(self.opponents, key=self.evaluate)
        logger.debug(f"Best target selected: {best_target.slug}")
        return best_target


def calculate_score(
    config: UserMonsterEntry, user: Monster, opponent: Monster
) -> ScoreResult:
    """Calculate score for an opponent based on config weights and attributes."""

    breakdown: dict[str, float] = {}
    breakdown["hp_ratio"] = opponent.hp_ratio * (config.health_weight or 0.0)
    breakdown["armour"] = opponent.armour * (config.armour_weight or 0.0)
    breakdown["dodge"] = opponent.dodge * (config.dodge_weight or 0.0)
    breakdown["melee"] = opponent.melee * (config.melee_weight or 0.0)
    breakdown["ranged"] = opponent.ranged * (config.ranged_weight or 0.0)
    breakdown["speed"] = opponent.speed * (config.speed_weight or 0.0)

    # Status effects
    status_effect_score = 0.0
    if config.status_effects and config.status_effects_weight:
        for status in opponent.status.get_statuses():
            if status.slug in config.status_effects:
                status_effect_score += (
                    config.status_effects[status.slug]
                    * config.status_effects_weight
                )
    breakdown["status_effects"] = status_effect_score

    # Level difference
    level_difference_score = 0.0
    if config.level_difference_threshold and config.level_difference_weight:
        level_difference = opponent.level - user.level
        if abs(level_difference) >= config.level_difference_threshold:
            level_difference_score = (
                level_difference * config.level_difference_weight
            )
    breakdown["level_difference"] = level_difference_score

    total_score = sum(breakdown.values())
    return ScoreResult(total=total_score, breakdown=breakdown)
