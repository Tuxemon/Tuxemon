# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.combat import get_target_monsters
from tuxemon.event.conditions.common import CommonCondition
from tuxemon.prepare import RECHARGE_RANGE
from tuxemon.technique.techeffect import TechEffect, TechEffectResult

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.technique.technique import Technique


@dataclass
class CoolDownEffect(TechEffect):
    """
    CoolDown is an effect that modifies the next_use value of a monster's
    techniques, delaying their availability within a specified recharge range.

    Parameters:
        objectives: The targets (e.g. own_monster, enemy_monster, etc.), if
            single "enemy_monster" or "enemy_monster:own_monster"
        next_use: The Monster object that we are using this technique on.
        parameter: The Technique attribute to check (e.g. category, range, etc.)
        value: The value is the corresponding attribute value (e.g. animal for
            category)
    """

    name = "cooldown"
    objectives: str
    next_use: int
    parameter: str
    value: str

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:

        if not _is_next_use_valid(self.next_use):
            raise ValueError(
                f"{self.name}: {self.next_use} must be between {RECHARGE_RANGE}"
            )

        combat = tech.combat_state
        assert combat
        tech.hit = tech.accuracy >= combat._random_tech_hit.get(user, 0.0)
        if not tech.hit:
            return TechEffectResult(
                name=tech.name,
                success=False,
                damage=0,
                element_multiplier=0.0,
                should_tackle=False,
                extras=[],
            )

        objectives = self.objectives.split(":")
        monsters = get_target_monsters(objectives, tech, user, target)
        moves_to_update = [move for mon in monsters for move in mon.moves]

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

        _update_moves(moves_to_update, self.next_use)
        if self.next_use > 0:
            tech.next_use -= 1

        return TechEffectResult(
            name=tech.name,
            success=True,
            damage=0,
            element_multiplier=0.0,
            should_tackle=False,
            extras=[],
        )


def _is_next_use_valid(next_use: int) -> bool:
    return RECHARGE_RANGE[0] <= next_use <= RECHARGE_RANGE[1]


def _update_moves(moves: list[Technique], next_use: int) -> None:
    for move in moves:
        if next_use == 0:
            move.next_use -= 1
        else:
            if move.next_use <= move.recharge_length:
                move.next_use = min(
                    move.next_use + next_use, RECHARGE_RANGE[1]
                )
