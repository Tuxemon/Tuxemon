# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, TechEffectResult
from tuxemon.formula import simple_damage_calculate
from tuxemon.locale.locale import T
from tuxemon.menu.formatter import CurrencyFormatter

if TYPE_CHECKING:
    from tuxemon.entity.npc import NPC
    from tuxemon.monster.monster import Monster
    from tuxemon.session import Session
    from tuxemon.technique.technique import Technique


@dataclass
class MoneyEffect(CoreEffect):
    """
    Applies the "money" effect to a technique.

    This effect either rewards the player with money if the technique
    successfully hits, or damages the user monster if the technique fails.
    The amount of money gained or damage dealt is equal to the calculated
    damage value.

    **Example**

    .. code-block:: json

        "effects": [
            "money"
        ]
    """

    name = "money"

    def apply_tech_target(
        self, session: Session, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:
        extra: list[str] = []
        player = user.get_owner()
        hit = session.client.combat_session.get_tech_hit(user)
        tech.hit = tech.accuracy >= hit

        damage = simple_damage_calculate(tech, user, target)[0]

        if tech.hit:
            amount = damage
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
