# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, TechEffectResult
from tuxemon.event.conditions.common import CommonCondition
from tuxemon.platform.const.sizes import RECHARGE_RANGE

if TYPE_CHECKING:
    from tuxemon.monster.monster import Monster
    from tuxemon.session import Session
    from tuxemon.technique.technique import Technique


@dataclass
class CooldownModifierEffect(CoreEffect):
    """
    Applies a cooldown to a monster's techniques, delaying their availability
    within a specified recharge range.

    **Parameters**

    - ``objectives``: The targets affected (e.g. ``own_monster``, ``enemy_monster``,
      or a combination like ``enemy_monster:own_monster``).
    - ``current_cooldown``: The number of turns to delay before the technique can be used
      again. Must be within ``RECHARGE_RANGE``.
    - ``parameter``: The technique attribute to check (e.g. ``category``, ``range``, etc.).
    - ``value``: The expected attribute value (e.g. ``animal`` for category).

    **Example**

    .. code-block:: json

        "effects": [
            "cooldown_modifier enemy_monster 2 category animal"
        ]
    """

    name = "cooldown_modifier"
    objectives: str
    current_cooldown: int
    parameter: str
    value: str

    def apply_tech_target(
        self, session: Session, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:

        if not RECHARGE_RANGE[0] <= self.current_cooldown <= RECHARGE_RANGE[1]:
            raise ValueError(
                f"{self.name}: {self.current_cooldown} must be between {RECHARGE_RANGE}"
            )

        hit = session.client.combat_session.get_tech_hit(user)
        tech.hit = tech.accuracy >= hit
        if not tech.hit:
            return TechEffectResult(name=tech.name)

        objectives = self.objectives.split(":")
        monsters = session.client.combat_session.get_target_monsters(
            objectives, user, target
        )
        moves_to_update = [
            move for mon in monsters for move in mon.moves.get_moves()
        ]

        if self.parameter == "types":
            moves_to_update = [
                move for move in moves_to_update if move.has_type(self.value)
            ]
        else:
            moves_to_update = [
                move
                for move in moves_to_update
                if not CommonCondition().check_parameter(
                    move, self.parameter, self.value
                )
            ]

        _update_moves(moves_to_update, self.current_cooldown)
        if self.current_cooldown > 0:
            tech.cooldown.tick()

        return TechEffectResult(name=tech.name, success=True)


def _update_moves(moves: list[Technique], current_cooldown: int) -> None:
    for move in moves:
        cd = move.cooldown

        if cd.locked:
            continue

        if current_cooldown == 0:
            if cd.delay_turns > 0:
                continue

            tick_amount = int(1 * cd.multiplier)
            cd.remaining = max(cd.min_remaining, cd.remaining - tick_amount)
            continue

        if cd.remaining <= cd.duration:
            added = int(current_cooldown * cd.multiplier)

            cd.remaining = max(
                cd.min_remaining, min(cd.remaining + added, RECHARGE_RANGE[1])
            )
