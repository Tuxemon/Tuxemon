# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon import formula
from tuxemon.core.core_effect import CoreEffect, TechEffectResult

if TYPE_CHECKING:
    from tuxemon.monster.monster import Monster
    from tuxemon.session import Session
    from tuxemon.technique.technique import Technique


@dataclass
class PhotogenesisEffect(CoreEffect):
    """
    Applies the "photogenesis" effect to a technique.

    This effect heals the user based on the time of day, with maximum
    healing occurring at the specified ``peak_hour``. Healing is skipped
    if the user is indoors, the technique misses, or the user is already
    at full health.

    **Parameters**

    - ``start_hour``: The hour when healing begins.
    - ``peak_hour``: The hour of maximum healing.
    - ``end_hour``: The hour when healing ends.

    **Example**

    .. code-block:: json

        "effects": [
            "photogenesis 18 0 6"
        ]
    """

    name = "photogenesis"
    start_hour: int
    peak_hour: int
    end_hour: int

    def apply_tech_target(
        self, session: Session, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:

        if session.client.map_manager.map_inside:
            return TechEffectResult(name=tech.name)

        hit = session.client.combat_session.get_tech_hit(user)
        extra: list[str] = []

        tech.hit = tech.accuracy >= hit

        if not tech.hit:
            return TechEffectResult(name=tech.name)

        if user.hp_ratio >= 1.0:
            extra = ["combat_full_health"]
            return TechEffectResult(name=tech.name, success=True, extras=extra)

        hour = session.time.get_time_variables().hour
        hp = user.shape.attributes.hp
        max_multiplier = hp / 2

        multiplier = formula.calculate_time_based_multiplier(
            hour=hour,
            peak_hour=self.peak_hour,
            max_multiplier=max_multiplier,
            start=self.start_hour,
            end=self.end_hour,
        )

        factors = {self.name: multiplier}

        heal = formula.simple_heal(tech, user, factors)
        if heal == 0:
            return TechEffectResult(name=tech.name)

        heal_amount = min(heal, user.missing_hp)
        user.current_hp += heal_amount
        return TechEffectResult(name=tech.name, success=True)
