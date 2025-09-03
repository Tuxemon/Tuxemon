# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon import formula
from tuxemon.core.core_effect import CoreEffect, TechEffectResult
from tuxemon.locale import T
from tuxemon.menu.formatter import CurrencyFormatter

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.npc import NPC
    from tuxemon.session import Session
    from tuxemon.technique.technique import Technique


@dataclass
class MoneyEffect(CoreEffect):
    """
    A tech effect that rewards the player with money if successful,
    or damages the monster if it fails.

    The amount of money rewarded or damage dealt is equal to the
    calculated damage.
    """

    name = "money"

    def apply_tech_target(
        self, session: Session, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:
        extra: list[str] = []
        player = user.get_owner()
        hit = session.client.combat_session.get_tech_hit(user)
        tech.hit = tech.accuracy >= hit

        damage, mult = formula.simple_damage_calculate(tech, user, target)

        if tech.hit:
            amount = int(damage * mult)
            _give_money(session, player, amount)
            formatter = CurrencyFormatter()
            formatted_amount = formatter.format(amount)
            params = {"name": user.name.upper(), "gold": formatted_amount}
            extra = [T.format("combat_state_gold", params)]
        else:
            user.current_hp = max(0, user.current_hp - damage)
        return TechEffectResult(
            name=tech.name,
            success=tech.hit,
            should_tackle=tech.hit,
            extras=extra,
        )


def _give_money(session: Session, character: NPC, amount: int) -> None:
    recipient = "player" if character.is_player else character.slug
    client = session.client.event_engine
    var = [recipient, amount]
    client.execute_action("modify_money", var, True)
