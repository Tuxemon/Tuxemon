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
class PropHealingEffect(CoreEffect):
    """
    Applies the "prop_healing" effect to a technique.

    This effect restores HP to one or more monsters based on a percentage
    of the user's maximum HP. It allows healing to scale with the user's
    durability rather than being a fixed value.

    **Parameters**

    - ``objectives``: Colon-separated string specifying which monsters are
      healed. Examples:
      - ``own_monster`` → heals only the user.
      - ``enemy_monster`` → heals only the target.
      - ``enemy_monster:own_monster`` → heals both the user and the target.
    - ``proportional``: Float value between 0 and 1 representing the fraction
      of the user's maximum HP to restore (e.g., ``0.25`` for 25%).

    **Example**

    .. code-block:: json

        "effects": [
            "prop_healing own_monster 0.25"
        ]
    """

    name = "prop_healing"
    objectives: str
    proportional: float

    def apply_tech_target(
        self, session: Session, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:

        if not 0 <= self.proportional <= 1:
            raise ValueError(f"{self.proportional} must be between 0 and 1")

        monsters: list[Monster] = []
        hit = session.client.combat_session.get_tech_hit(user)

        objectives = self.objectives.split(":")
        tech.hit = tech.accuracy >= hit
        reference_hp = user.hp

        if tech.hit:
            monsters = session.client.combat_session.get_target_monsters(
                objectives, user, target
            )

        if monsters:
            amount = int((reference_hp) * self.proportional)
            for monster in monsters:
                monster.current_hp = min(
                    monster.hp, monster.current_hp + amount
                )

        return TechEffectResult(name=tech.name, success=tech.hit)
