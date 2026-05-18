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
class CooldownMinimumEffect(CoreEffect):
    """
    Sets a minimum cooldown value for affected techniques, preventing their
    cooldown from being reduced below the specified threshold. Useful for
    enforcing a baseline recharge time even under haste or multiplier effects.

    **Parameters**

    - ``objectives``: The targets affected (e.g. ``own_monster``, ``enemy_monster``).
    - ``minimum``: The minimum cooldown value that cannot be undercut.

    **Example**

    .. code-block:: json

        "effects": [
            "cooldown_minimum own_monster 2"
        ]
    """

    name = "cooldown_minimum"
    objectives: str
    minimum: int

    def apply_tech_target(
        self, session: Session, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:
        monsters = session.client.combat_session.get_target_monsters(
            self.objectives.split(":"), user, target
        )
        for mon in monsters:
            for move in mon.moves.get_moves():
                move.cooldown.min_remaining = self.minimum

        return TechEffectResult(name=tech.name, success=True)
