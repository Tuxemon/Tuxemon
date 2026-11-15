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
class CooldownSwapEffect(CoreEffect):
    """
    Swaps the current cooldown values of two techniques on the affected monster,
    allowing strategic redistribution of recharge times.

    **Parameters**

    - ``objectives``: The targets affected (e.g. ``own_monster``).
    - ``param_a``: The first technique attribute to match (e.g. ``melee``).
    - ``param_b``: The second technique attribute to match (e.g. ``ranged``).

    **Example**

    .. code-block:: json

        "effects": [
            "cooldown_swap own_monster melee ranged"
        ]
    """

    name = "cooldown_swap"
    objectives: str
    param_a: str
    param_b: str

    def apply_tech_target(
        self, session: Session, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:
        monsters = session.client.combat_session.get_target_monsters(
            self.objectives.split(":"), user, target
        )

        for mon in monsters:
            moves = mon.moves.get_moves()
            moveA = next((m for m in moves if m.sort == self.param_a), None)
            moveB = next((m for m in moves if m.sort == self.param_b), None)

            if moveA and moveB:
                moveA.cooldown.swap_with(moveB.cooldown)

        return TechEffectResult(name=tech.name, success=True)
