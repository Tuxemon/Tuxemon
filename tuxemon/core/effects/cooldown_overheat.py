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
class CooldownOverheatEffect(CoreEffect):
    """
    Increases the base cooldown duration of affected techniques, making them take
    longer to recharge after use.

    **Parameters**

    - ``objectives``: The targets affected (e.g. ``own_monster``, ``enemy_monster``).
    - ``amount``: The number of turns to add to each technique's cooldown duration.

    **Example**

    .. code-block:: json

        "effects": [
            "cooldown_overheat own_monster 1 category fire"
        ]
    """

    name = "cooldown_overheat"
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
                cd = move.cooldown
                if cd.locked:
                    continue

                cd.duration += self.amount
                cd.min_remaining = max(cd.min_remaining, self.amount)

        return TechEffectResult(name=tech.name, success=True)
