# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon import formula
from tuxemon.technique.techeffect import TechEffect, TechEffectResult

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.technique.technique import Technique


class MoneyEffectResult(TechEffectResult):
    pass


@dataclass
class MoneyEffect(TechEffect):
    """
    If it fails, then the monster is damaged.
    If it works, then the player gets money.
    quantity damage = quantity money

    """

    name = "money"

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> MoneyEffectResult:
        done: bool = False
        player = self.session.player
        value = float(player.game_variables["random_tech_hit"])
        damage, mult = formula.simple_damage_calculate(tech, user, target)
        hit = tech.accuracy >= 5
        print(tech.accuracy, value)
        if hit:
            done = True
            user.current_hp -= damage
        else:
            done = False
            tech.advance_counter_success()
            amount = int(damage * mult)
            player.give_money(amount)
            player.game_variables["gold_digger"] = damage
        return {"success": done}
