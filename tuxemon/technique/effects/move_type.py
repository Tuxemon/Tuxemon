# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.technique.techeffect import TechEffect, TechEffectResult

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.technique.technique import Technique


@dataclass
class MoveTypeEffect(TechEffect):
    """
    Move Type Effect:
    This effect changes the type of a move to match the type of the monster
    using it. For example, if a Fire-type monster uses a move with this effect,
    the move becomes a Fire-type attack. This provides a reliable way for
    monsters to deal damage of their own type, which can be beneficial in battle.

    The direction of this effect can be either "own_monster" (the monster using
    the move) or "enemy_monster" (the target of the move). This determines whose
    type the move will match.

    Example:
    A Fire-type monster uses a move with this effect.
    The move becomes a Fire-type attack, dealing Fire-type damage and benefiting
    from same-type attack bonus (STAB).

    Attributes:
        direction: The direction, either "own_monster" or "enemy_monster".
    """

    name = "move_type"
    direction: str

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:

        if self.direction == "own_monster":
            tech.types = user.types
        elif self.direction == "enemy_monster":
            tech.types = target.types
        else:
            raise ValueError(
                f"{self.direction} must be 'own_monster' or 'enemy_monster'"
            )

        return TechEffectResult(
            name=tech.name,
            success=True,
            damage=0,
            element_multiplier=0.0,
            should_tackle=False,
            extras=[],
        )
