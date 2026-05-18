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
class CooldownBalanceEffect(CoreEffect):
    """
    Redistributes cooldown evenly across all affected techniques by setting each
    technique's cooldown to the average of the group's current values.

    **Parameters**

    - ``objectives``: The targets affected (e.g. ``own_monster``, ``enemy_monster``).

    **Example**

    .. code-block:: json

        "effects": [
            "cooldown_balance own_monster"
        ]
    """

    name = "cooldown_balance"
    objectives: str

    def apply_tech_target(
        self, session: Session, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:
        monsters = session.client.combat_session.get_target_monsters(
            self.objectives.split(":"), user, target
        )

        for mon in monsters:
            moves = mon.moves.get_moves()
            if not moves:
                continue

            avg = sum(m.cooldown.remaining for m in moves) // len(moves)

            for move in moves:
                if move.cooldown.locked:
                    continue
                move.cooldown.remaining = max(move.cooldown.min_remaining, avg)

        return TechEffectResult(name=tech.name, success=True)
