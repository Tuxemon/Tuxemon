# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, TechEffectResult
from tuxemon.event.conditions.common import CommonCondition
from tuxemon.prepare import RECHARGE_RANGE

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.session import Session
    from tuxemon.technique.technique import Technique


@dataclass
class CoolDownEffect(CoreEffect):
    """
    CoolDown is an effect that modifies the current_cooldown value of a monster's
    techniques, delaying their availability within a specified recharge range.

    Parameters:
        objectives: The targets (e.g. own_monster, enemy_monster, etc.), if
            single "enemy_monster" or "enemy_monster:own_monster"
        current_cooldown: The Monster object that we are using this technique on.
        parameter: The Technique attribute to check (e.g. category, range, etc.)
        value: The value is the corresponding attribute value (e.g. animal for
            category)
    """

    name = "cooldown"
    objectives: str
    current_cooldown: int
    parameter: str
    value: str

    def apply_tech_target(
        self, session: Session, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:

        if not _is_next_use_valid(self.current_cooldown):
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
            tech.current_cooldown -= 1

        return TechEffectResult(name=tech.name, success=True)


def _is_next_use_valid(current_cooldown: int) -> bool:
    return RECHARGE_RANGE[0] <= current_cooldown <= RECHARGE_RANGE[1]


def _update_moves(moves: list[Technique], current_cooldown: int) -> None:
    for move in moves:
        if current_cooldown == 0:
            move.current_cooldown -= 1
        else:
            if move.current_cooldown <= move.cooldown_duration:
                move.current_cooldown = min(
                    move.current_cooldown + current_cooldown, RECHARGE_RANGE[1]
                )
