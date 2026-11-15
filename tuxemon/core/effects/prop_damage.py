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
class PropDamageEffect(CoreEffect):
    """
    Applies the "prop_damage" effect to a technique.

    This effect deals proportional damage to one or more monsters based on
    a percentage of the target's maximum HP. It allows damage to scale with
    the target's durability rather than being a fixed value.

    **Parameters**

    - ``objectives``: Colon-separated string specifying which monsters are
      affected. Examples:
      - ``enemy_monster`` → damages only the enemy.
      - ``enemy_monster:own_monster`` → damages both the enemy and the user.
    - ``proportional``: Float value between 0 and 1 representing the fraction
      of the target's maximum HP to use as damage (e.g., ``0.25`` for 25%).

    **Example**

    .. code-block:: json

        "effects": [
            "prop_damage enemy_monster 0.25"
        ]
    """

    name = "prop_damage"
    objectives: str
    proportional: float

    def apply_tech_target(
        self, session: Session, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:

        if not 0 <= self.proportional <= 1:
            raise ValueError(f"{self.proportional} must be between 0 and 1")

        damage = 0
        monsters: list[Monster] = []

        objectives = self.objectives.split(":")
        hit = session.client.combat_session.get_tech_hit(user)
        tech.hit = tech.accuracy >= hit
        reference_hp = target.hp

        if tech.hit:
            monsters = session.client.combat_session.get_target_monsters(
                objectives, user, target
            )

        if monsters:
            damage = int(float(reference_hp) * self.proportional)
            for monster in monsters:
                monster.current_hp = max(0, monster.current_hp - damage)
                # to avoid double registration in the self._damage_map
                if monster != target:
                    session.client.combat_session.enqueue_damage(
                        user, monster, damage
                    )

        return TechEffectResult(
            name=tech.name,
            damage=damage,
            should_tackle=tech.hit,
            success=tech.hit,
        )
