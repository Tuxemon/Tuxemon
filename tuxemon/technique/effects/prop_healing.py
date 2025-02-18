# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.combat import get_target_monsters
from tuxemon.technique.techeffect import TechEffect, TechEffectResult

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.technique.technique import Technique


@dataclass
class PropHealingEffect(TechEffect):
    """
    Proportional Healing:
    This effect does healing to the enemy equal to % of the user's maximum HP.

    Parameters:
        objectives: The targets (e.g. own_monster, enemy_monster, etc.), if
            single "enemy_monster" or "enemy_monster:own_monster"
        proportional: The percentage of the max HP (from 0 to 1)

    eg prop_healing own_monster,0.25 (1/4 max enemy HP)

    """

    name = "prop_healing"
    objectives: str
    proportional: float

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:

        if not 0 <= self.proportional <= 1:
            raise ValueError(f"{self.proportional} must be between 0 and 1")

        monsters: list[Monster] = []
        combat = tech.combat_state
        assert combat

        objectives = self.objectives.split(":")
        tech.hit = tech.accuracy >= combat._random_tech_hit.get(user, 0.0)
        reference_hp = user.hp

        if tech.hit:
            monsters = get_target_monsters(objectives, tech, user, target)

        if monsters:
            amount = int((reference_hp) * self.proportional)
            for monster in monsters:
                monster.current_hp = min(
                    monster.hp, monster.current_hp + amount
                )

        return TechEffectResult(
            name=tech.name,
            damage=0,
            element_multiplier=0.0,
            should_tackle=False,
            success=tech.hit,
            extras=[],
        )
