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
class CooldownMultiplierEffect(CoreEffect):
    """
    Modifies the cooldown tick speed of affected techniques by applying a
    multiplier. Values greater than 1.0 accelerate cooldown recovery, while
    values below 1.0 slow it down.

    **Parameters**

    - ``objectives``: The targets affected (e.g. ``own_monster``, ``enemy_monster``).
    - ``multiplier``: The factor applied to cooldown ticking (e.g. ``1.5``, ``2.0``).

    **Example**

    .. code-block:: json

        "effects": [
            "cooldown_multiplier own_monster 1.5"
        ]
    """

    name = "cooldown_multiplier"
    objectives: str
    multiplier: float

    def apply_tech_target(
        self, session: Session, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:
        monsters = session.client.combat_session.get_target_monsters(
            self.objectives.split(":"), user, target
        )
        for mon in monsters:
            for move in mon.moves.get_moves():
                move.cooldown.multiplier = self.multiplier

        return TechEffectResult(name=tech.name, success=True)
