# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Sequence

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
        if tech.combat_state is None or user.owner is None:
            raise ValueError()
        player = user.owner
        value = float(player.game_variables["random_tech_hit"])
        hit = tech.accuracy >= value
        if hit:
            tech.advance_counter_success()
            damage, mult = formula.simple_damage_calculate(tech, user, target)
            # 2 vs 2, damage both monsters
            if player.max_position > 1:
                monsters: Sequence[Monster] = []
                combat = tech.combat_state
                human = combat.monsters_in_play_human
                opponent = combat.monsters_in_play_ai
                if player.isplayer:
                    monsters = opponent
                else:
                    monsters = human
                for mon in monsters:
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
