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
class SacrificeEffect(CoreEffect):
    """
    Applies the "sacrifice" effect to a technique.

    This effect causes the user monster to faint by sacrificing its current
    HP. The amount of HP sacrificed is also dealt as damage to the target.
    The multiplier determines what fraction of the user's current HP is
    converted into damage.

    **Parameters**

    - ``multiplier``: Float value between 0 and 1 representing the fraction
      of the user's current HP to sacrifice.
      - ``1.0`` → sacrifices all current HP.
      - ``0.5`` → sacrifices half of current HP.

    **Example**

    .. code-block:: json

        "effects": [
            "sacrifice 1"
        ]
    """

    name = "sacrifice"
    multiplier: float

    def apply_tech_target(
        self, session: Session, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:

        if not 0 <= self.multiplier <= 1:
            raise ValueError("Multiplier must be a float between 0 and 1")

        hit = session.client.combat_session.get_tech_hit(user)
        tech.hit = tech.accuracy >= hit

        if tech.hit:
            damage = int(user.current_hp * self.multiplier)
            user.current_hp = 0
            target.current_hp = max(0, target.current_hp - damage)
        else:
            damage = 0

        return TechEffectResult(
            name=tech.name,
            damage=damage,
            should_tackle=tech.hit,
            success=tech.hit,
        )
