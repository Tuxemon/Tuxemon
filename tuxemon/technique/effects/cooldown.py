# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.db import ElementType
from tuxemon.event.conditions.common import CommonCondition
from tuxemon.prepare import RECHARGE_RANGE
from tuxemon.technique.techeffect import TechEffect, TechEffectResult

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.technique.technique import Technique


class CoolDownEffectResult(TechEffectResult):
    pass


@dataclass
class CoolDownEffect(TechEffect):
    """
    CoolDown is an effect that modifies the next_use value of a monster's
    techniques, delaying their availability within a specified recharge range.
    This effect can be applied to either the user's monster or the target
    monster, depending on the objective.

    The effect targets specific techniques based on the provided parameter
    and value, where the parameter is a Technique attribute (e.g., category,
    range) and the value is the corresponding attribute value (e.g., 'animal'
    for category, 'special' for sort).
    """

    name = "cooldown"
    objective: str
    next_use: int
    parameter: str
    value: str

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> CoolDownEffectResult:

        if not _is_next_use_valid(self.next_use):
            raise ValueError(
                f"{self.name}: {self.next_use} must be between {RECHARGE_RANGE}"
            )

        tech.hit = tech.accuracy >= (
            tech.combat_state._random_tech_hit.get(user, 0.0)
            if tech.combat_state
            else 0.0
        )
        if not tech.hit:
            return {
                "success": False,
                "damage": 0,
                "element_multiplier": 0.0,
                "should_tackle": False,
                "extra": None,
            }

        monster = user if self.objective == "user" else target
        moves_to_update = monster.moves
        combat = tech.combat_state
        character = monster.owner
        assert combat and character

        if character.max_position > 1 and tech.target["enemy_team"]:
            monsters = (
                combat.monsters_in_play_left
                if monster in combat.monsters_in_play_right
                else combat.monsters_in_play_right
            )
            moves_to_update = [move for mon in monsters for move in mon.moves]

        if self.parameter == "types":
            moves_to_update = [
                move
                for move in moves_to_update
                if move.has_type(ElementType(self.value))
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

        return {
            "success": True,
            "damage": 0,
            "element_multiplier": 0.0,
            "should_tackle": False,
            "extra": None,
        }


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
