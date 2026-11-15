# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, TechEffectResult

if TYPE_CHECKING:
    from tuxemon.monster.monster import Monster
    from tuxemon.session import Session
    from tuxemon.technique.technique import Technique


@dataclass
class CooldownChargeEffect(CoreEffect):
    """
    Increases the stored charge value of affected techniques, allowing them to
    become more powerful the longer they remain unused.

    **Parameters**

    - ``objectives``: The targets affected (e.g. ``own_monster``, ``enemy_monster``).
    - ``amount``: The amount of charge to add to each technique.

    **Example**

    .. code-block:: json

        "effects": [
            "cooldown_charge own_monster 1 category ranged"
        ]
    """

    name = "cooldown_charge"
    objectives: str
    amount: int

    def apply_tech_target(
        self, session: Session, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:
        monsters = session.client.combat_session.get_target_monsters(
            self.objectives.split(":"), user, target
        )

        for mon in monsters:
            for move in mon.moves.get_moves():
                if move.cooldown.locked:
                    continue

                charge_gain = self.amount
                charge_gain = int(charge_gain * move.cooldown.multiplier)
                charge_gain += move.cooldown.delay_turns
                move.cooldown.charge += charge_gain

        return TechEffectResult(name=tech.name, success=True)
