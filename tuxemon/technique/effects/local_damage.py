# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass

from tuxemon import formula
from tuxemon.monster import Monster
from tuxemon.technique.techeffect import TechEffect, TechEffectResult
from tuxemon.technique.technique import Technique


class LocalDamageEffectResult(TechEffectResult):
    damage: int
    element_multiplier: float
    should_tackle: bool


@dataclass
class LocalDamageEffect(TechEffect):
    """
    Apply damage, but it allows different output depending on the
    technique used. Originally "particular_damage", but it was
    too verbose.

    Parameters:
        user: The Monster object that used this technique.
        target: The Monster object that we are using this technique on.

    Returns:
        Dict summarizing the result.

    """

    name = "local_damage"

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> LocalDamageEffectResult:
        player = self.session.player
        value = float(player.game_variables["random_tech_hit"])
        hit = tech.accuracy >= value
        if hit or tech.is_area:
            tech.advance_counter_success()
            damage, mult = formula.simple_damage_calculate(tech, user, target)
            if not hit:
                damage //= 2
            # land of ifs
            # tech: panjandrum
            if tech.slug == "panjandrum":
                damage = formula.damage_panjandrum(target)
            target.current_hp -= damage
        else:
            damage = 0
            mult = 1.0

        return {
            "damage": damage,
            "element_multiplier": mult,
            "should_tackle": bool(damage),
            "success": bool(damage),
        }
