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
class MoveTypeEffect(CoreEffect):
    """
    Applies the "move_type" effect to a technique.

    This effect changes the type of a move to match the type of either the
    user or the target monster. For example, if a Fire-type monster uses a
    move with this effect, the move becomes a Fire-type attack, benefiting
    from same-type attack bonus (STAB).

    **Parameters**

    - ``direction``: Determines whose type the move will adopt.
      - ``own_monster``: The move takes on the type(s) of the user monster.
      - ``enemy_monster``: The move takes on the type(s) of the target monster.

    **Example**

    .. code-block:: json

        "effects": [
            "move_type own_monster"
        ]
    """

    name = "move_type"
    direction: str

    def apply_tech_target(
        self, session: Session, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:

        if self.direction == "own_monster":
            slugs = user.types.get_type_slugs()
        elif self.direction == "enemy_monster":
            slugs = target.types.get_type_slugs()
        else:
            raise ValueError(
                f"{self.direction} must be 'own_monster' or 'enemy_monster'"
            )

        tech.types.set_types(slugs)
        return TechEffectResult(name=tech.name, success=True)
