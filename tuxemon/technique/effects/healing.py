# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass

from tuxemon.monster import Monster
from tuxemon.technique.techeffect import TechEffect, TechEffectResult
from tuxemon.technique.technique import Technique


class HealingEffectResult(TechEffectResult):
    pass


@dataclass
class HealingEffect(TechEffect):
    """
    Healing is based on healing power.

    Healing power indicates that the technique heals its user an
    amount equal to the damage done by a reliable technique of
    the same power.

    """

    name = "healing"

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> HealingEffectResult:
        heal: int = 0
        player = self.session.player
        value = float(player.game_variables["random_tech_hit"])
        hit = tech.accuracy >= value
        if isinstance(tech.healing_power, int):
            heal = (7 + user.level) * tech.healing_power
        diff = user.hp - user.current_hp
        if hit:
            tech.advance_counter_success()
            if diff > 0:
                if heal >= diff:
                    user.current_hp = user.hp
                else:
                    user.current_hp += heal
                return {"success": True}
            else:
                return {"success": False}
        else:
            return {"success": False}
