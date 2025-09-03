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
class ReverseEffect(CoreEffect):
    """
    Reverse "Switch" effect:
    it returns the original monster type.

    Parameters:
        objectives: The targets (e.g. own_monster, enemy_monster, etc.), if
            single "enemy_monster" or "enemy_monster:own_monster"

    eg reverse enemy_monster
    eg reverse enemy_monster:own_monster
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
