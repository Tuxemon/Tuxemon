# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.combat import get_target_monsters
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
        combat = tech.combat_state
        assert combat

        tech.hit = tech.accuracy >= combat._random_tech_hit.get(user, 0.0)

        if not tech.hit:
            return TechEffectResult(name=tech.name, success=tech.hit)

        objectives = self.objectives.split(":")
        monsters = get_target_monsters(objectives, tech, user, target)
        for monster in monsters:
            monster.reset_types()

        return TechEffectResult(name=tech.name, success=True)
