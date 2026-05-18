# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.formula import simple_damage_multiplier
from tuxemon.platform.const.sizes import POWER_RANGE
from tuxemon.technique.technique import Technique

if TYPE_CHECKING:
    from tuxemon.ai.ai import SingleTechnique
    from tuxemon.monster.monster import Monster
    from tuxemon.session import Session

logger = logging.getLogger(__name__)


@dataclass
class TechniqueScoreResult:
    total: float
    breakdown: dict[str, float]


class TechniqueTracker:
    def __init__(self, session: Session, moves: list[Technique]):
        self.session = session
        self.moves = moves

    def get_valid_moves(
        self, opponents: list[Monster]
    ) -> list[tuple[Technique, Monster]]:
        """Returns valid techniques and their corresponding opponents."""
        return [
            (mov, opponent)
            for mov in self.moves
            for opponent in opponents
            if mov.can_use(self.session, opponent)
        ]

    def evaluate_technique(
        self,
        user: Monster,
        technique: Technique,
        opponent: Monster,
        config: SingleTechnique,
    ) -> float:
        """
        Evaluate the effectiveness of a technique against a specific opponent.
        """
        result = technique_score(user, technique, opponent, config)
        logger.debug(
            f"Technique evaluation for {technique.slug} vs {opponent.slug}: {result.breakdown}"
        )
        logger.debug(f"Final technique score: {result.total}")
        return result.total


def technique_score(
    user: Monster,
    technique: Technique,
    opponent: Monster,
    config: SingleTechnique,
) -> TechniqueScoreResult:
    """Calculate technique score with breakdown."""

    breakdown: dict[str, float] = {}

    # Elemental effectiveness
    effectiveness_score = 0.0
    if config.elemental_multiplier_weight:
        effectiveness_score = (
            simple_damage_multiplier(
                technique.types.current, opponent.types.current
            )
            * config.elemental_multiplier_weight
        )
    elemental_health = config.elemental_health_threshold
    elemental_scaling = config.elemental_health_scaling
    if elemental_health and elemental_scaling:
        if opponent.current_hp > opponent.hp * elemental_health:
            effectiveness_score *= elemental_scaling
    breakdown["effectiveness"] = effectiveness_score

    # Range bonus
    type_bonus = getattr(config, f"{technique.range}_bonus", 0.0)
    breakdown["type_bonus"] = type_bonus

    # Power
    power_score = 0.0
    if config.power_weight:
        normalized_power = technique.power / POWER_RANGE[1]
        power_score = normalized_power * config.power_weight
    breakdown["power"] = power_score

    # Accuracy
    accuracy_score = 0.0
    if config.accuracy_weight:
        accuracy_score = technique.accuracy * config.accuracy_weight
    breakdown["accuracy"] = accuracy_score

    # Healing
    healing_score = 0.0
    health_priority = config.health_priority_threshold
    healing_penalty = config.healing_penalty_threshold
    is_healing_move = technique.healing_power > 0.0 or technique.power == 0.0

    if health_priority and is_healing_move:
        if user.hp_ratio < health_priority and config.healing_weight:
            healing_score = technique.healing_power * config.healing_weight
    if healing_penalty and is_healing_move:
        if user.hp_ratio > healing_penalty and config.healing_penalty_weight:
            healing_score = (
                -technique.healing_power * config.healing_penalty_weight
            )
    breakdown["healing"] = healing_score

    total_score = sum(breakdown.values())

    logger.debug(
        f"Technique score breakdown for {technique.slug}: {breakdown}"
    )
    logger.debug(f"Final technique score: {total_score}")
    return TechniqueScoreResult(total=total_score, breakdown=breakdown)
