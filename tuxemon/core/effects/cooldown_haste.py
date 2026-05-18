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
class CooldownHasteEffect(CoreEffect):
    """
    Accelerates cooldown recovery for a specified number of turns, causing affected
    techniques to recharge faster than normal.

    **Parameters**

    - ``objectives``: The targets affected (e.g. ``own_monster``, ``enemy_monster``).
    - ``turns``: How many turns the haste effect lasts.
    - ``multiplier``: How much faster cooldown ticks (e.g. 1.5, 2.0, 3.0).

    **Example**

    .. code-block:: json

        "effects": [
            "cooldown_haste own_monster 3 2.0"
        ]
    """

    name = "cooldown_haste"
    objectives: str
    turns: int
    multiplier: float

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

                cd.haste_turns = max(cd.haste_turns, self.turns)
                cd.multiplier = self.multiplier

        return TechEffectResult(name=tech.name, success=True)
