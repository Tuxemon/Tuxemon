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
class LifeSwapEffect(CoreEffect):
    """
    Applies the "life_swap" effect to a technique.

    This effect exchanges the current HP values of the user and the target.
    Each monster receives the other's HP, capped at its own maximum HP.

    **Example**

    .. code-block:: json

        "effects": [
            "life_swap"
        ]
    """

    name = "life_swap"

    def apply_tech_target(
        self, session: Session, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:
        hit = session.client.combat_session.get_tech_hit(user)
        tech.hit = tech.accuracy >= hit
        done = False
        if tech.hit:
            if not user.is_fainted and not target.is_fainted:
                hp_user, hp_target = user.current_hp, target.current_hp
                user.current_hp = min(user.hp, hp_target)
                target.current_hp = min(target.hp, hp_user)
                done = True
        return TechEffectResult(name=tech.name, success=done)
