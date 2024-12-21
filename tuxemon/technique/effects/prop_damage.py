# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.combat import get_target_monsters
from tuxemon.technique.techeffect import TechEffect, TechEffectResult

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.technique.technique import Technique


class PropDamageEffectResult(TechEffectResult):
    pass


@dataclass
class PropDamageEffect(TechEffect):
    """
    Proportional Damage:
    This effect does damage to the enemy equal to % of the target's maximum HP.

    Parameters:
        objectives: The targets (e.g. own_monster, enemy_monster, etc.), if
            single "enemy_monster" or "enemy_monster:own_monster"
        proportional: The percentage of the max HP (from 0 to 1)

    eg prop_damage enemy_monster,0.25 (1/4 max enemy HP)

    """

    name = "prop_damage"
    objectives: str
    proportional: float

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> PropDamageEffectResult:

        if not 0 <= self.proportional <= 1:
            raise ValueError(f"{self.proportional} must be between 0 and 1")

        damage = 0
        monsters: list[Monster] = []
        combat = tech.combat_state
        assert combat

        objectives = self.objectives.split(":")
        tech.hit = tech.accuracy >= combat._random_tech_hit.get(user, 0.0)
        reference_hp = target.hp

        if tech.hit:
            monsters = get_target_monsters(objectives, tech, user, target)

        if monsters:
            damage = int(float(reference_hp) * self.proportional)
            for monster in monsters:
                monster.current_hp = max(0, monster.current_hp - damage)
                # to avoid double registration in the self._damage_map
                if monster != target:
                    combat.enqueue_damage(user, monster, damage)

        return {
            "damage": damage,
            "element_multiplier": 0.0,
            "should_tackle": tech.hit,
            "success": tech.hit,
            "extra": None,
        }
