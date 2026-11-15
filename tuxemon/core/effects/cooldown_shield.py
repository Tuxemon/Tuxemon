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
class CooldownShieldEffect(CoreEffect):
    """
    Grants a cooldown shield to affected techniques, causing the next cooldown
    trigger to be ignored. The shield is consumed upon activation.

    **Parameters**

    - ``objectives``: The targets affected (e.g. ``own_monster``, ``enemy_monster``).

    **Example**

    .. code-block:: json

        "effects": [
            "cooldown_shield own_monster"
        ]
    """

    name = "cooldown_shield"
    objectives: str

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

                cd.shield = True

        return TechEffectResult(name=tech.name, success=True)
