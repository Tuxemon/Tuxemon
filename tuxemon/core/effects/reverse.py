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
class ReverseEffect(CoreEffect):
    """
    Applies the "reverse" effect to a technique.

    This effect resets the type(s) of one or more monsters back to their
    original default values. It is typically used to undo type-changing
    effects applied earlier in battle.

    **Parameters**

    - ``objectives``: Colon-separated string specifying which monsters are affected. Examples:
      - ``enemy_monster`` → resets only the enemy's type(s).
      - ``own_monster`` → resets only the user's type(s).
      - ``enemy_monster:own_monster`` → resets both the enemy's and the user's type(s).

    **Examples**

    .. code-block:: json

        "effects": [
            "reverse enemy_monster"
        ]

        "effects": [
            "reverse enemy_monster:own_monster"
        ]
    """

    name = "reverse"
    objectives: str

    def apply_tech_target(
        self, session: Session, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:
        hit = session.client.combat_session.get_tech_hit(user)

        tech.hit = tech.accuracy >= hit

        if not tech.hit:
            return TechEffectResult(name=tech.name, success=tech.hit)

        objectives = self.objectives.split(":")
        monsters = session.client.combat_session.get_target_monsters(
            objectives, user, target
        )
        for monster in monsters:
            monster.types.reset_to_default()

        return TechEffectResult(name=tech.name, success=True)
