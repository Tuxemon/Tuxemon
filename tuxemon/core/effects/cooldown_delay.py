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
class CooldownDelayEffect(CoreEffect):
    """
    Applies a cooldown delay to affected techniques, preventing their cooldown
    from beginning immediately. During the delay period, cooldown does not tick
    and techniques remain available until the delay expires.

    **Parameters**

    - ``objectives``: The targets affected (e.g. ``own_monster``, ``enemy_monster``).
    - ``turns``: The number of turns cooldown is delayed before ticking begins.

    **Example**

    .. code-block:: json

        "effects": [
            "cooldown_delay own_monster 2"
        ]
    """

    name = "cooldown_delay"
    objectives: str
    turns: int

    def apply_tech_target(
        self, session: Session, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:
        monsters = session.client.combat_session.get_target_monsters(
            self.objectives.split(":"), user, target
        )
        for mon in monsters:
            for move in mon.moves.get_moves():
                move.cooldown.delay_turns = max(
                    move.cooldown.delay_turns, self.turns
                )

        return TechEffectResult(name=tech.name, success=True)
