# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, TechEffectResult

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.session import Session
    from tuxemon.technique.technique import Technique


@dataclass
class LifeSwapEffect(CoreEffect):
    """
    Swaps the current HP amounts of the two monsters.

    Swaps the current HP amounts of the two monsters. The user receives
    the target's HP (up to the user's max HP), and the target receives
    the user's HP (up to the target's max HP).
    """

    name = "life_swap"

    def apply_tech_target(
        self, session: Session, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:
        tech.hit = tech.accuracy >= (
            tech.combat_state._random_tech_hit.get(user, 0.0)
            if tech.combat_state
            else 0.0
        )
        done = False
        if tech.hit:
            if not user.is_fainted and not target.is_fainted:
                hp_user, hp_target = user.current_hp, target.current_hp
                user.current_hp = min(user.hp, hp_target)
                target.current_hp = min(target.hp, hp_user)
                done = True
        return TechEffectResult(name=tech.name, success=done)
