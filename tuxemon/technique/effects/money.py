# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from tuxemon import formula
from tuxemon.locale import T
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
        extra: Optional[str] = None
        player = user.owner
        combat = tech.combat_state
        assert combat and player
        value = combat._random_tech_hit.get(user, 0.0)
        damage, mult = formula.simple_damage_calculate(tech, user, target)
        hit = tech.accuracy >= value
        if hit:
            user.current_hp -= damage
        else:
            amount = int(damage * mult)
            recipient = "player" if player.isplayer else player.slug
            client = self.session.client.event_engine
            var = [recipient, amount]
            client.execute_action("modify_money", var, True)
            params = {"name": user.name.upper(), "symbol": "$", "gold": amount}
            extra = T.format("combat_state_gold", params)
        return {
            "success": hit,
            "damage": 0,
            "element_multiplier": 0.0,
            "should_tackle": False,
            "extra": extra,
        }
