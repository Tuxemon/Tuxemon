# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon import formula
from tuxemon.locale import T
from tuxemon.technique.techeffect import TechEffect, TechEffectResult

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.npc import NPC
    from tuxemon.technique.technique import Technique


@dataclass
class MoneyEffect(TechEffect):
    """
    A tech effect that rewards the player with money if successful,
    or damages the monster if it fails.

    The amount of money rewarded or damage dealt is equal to the
    calculated damage.
    """

    name = "money"

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:
        extra: list[str] = []
        player = user.owner
        combat = tech.combat_state
        assert combat and player
        tech.hit = tech.accuracy >= combat._random_tech_hit.get(user, 0.0)

        damage, mult = formula.simple_damage_calculate(tech, user, target)

        if tech.hit:
            amount = int(damage * mult)
            self._give_money(player, amount)
            params = {"name": user.name.upper(), "symbol": "$", "gold": amount}
            extra = [T.format("combat_state_gold", params)]
        else:
            user.current_hp = max(0, user.current_hp - damage)
        return TechEffectResult(
            name=tech.name,
            success=tech.hit,
            damage=0,
            element_multiplier=0.0,
            should_tackle=tech.hit,
            extras=extra,
        )

    def _give_money(self, character: NPC, amount: int) -> None:
        recipient = "player" if character.isplayer else character.slug
        client = self.session.client.event_engine
        var = [recipient, amount]
        client.execute_action("modify_money", var, True)
