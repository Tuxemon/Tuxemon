# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon import formula
from tuxemon.technique.techeffect import TechEffect, TechEffectResult

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.technique.technique import Technique


class AreaEffectResult(TechEffectResult):
    pass


@dataclass
class AreaEffect(TechEffect):
    """
    Apply area damage.

    """

    name = "area"

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> AreaEffectResult:
        combat = tech.combat_state
        player = user.owner
        assert combat and player
        hit = tech.accuracy >= combat._random_tech_hit.get(user, 0.0)
        if hit:
            damage, mult = formula.simple_damage_calculate(tech, user, target)
            # Apply the damage to all the monsters on the opposite side
            if player.max_position > 1:
                monsters_to_damage = (
                    combat.monsters_in_play_left
                    if user in combat.monsters_in_play_right
                    else combat.monsters_in_play_right
                )
                for mon in monsters_to_damage:
                    mon.current_hp -= damage
                    combat.enqueue_damage(user, mon, damage)
            else:
                target.current_hp -= damage
        else:
            damage = 0
            mult = 1.0

        return {
            "damage": damage,
            "element_multiplier": mult,
            "should_tackle": bool(damage),
            "success": bool(damage),
            "extra": None,
        }
