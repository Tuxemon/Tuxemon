# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.combat import get_target_monsters, has_status
from tuxemon.technique.techeffect import TechEffect, TechEffectResult

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.technique.technique import Technique


class RemoveEffectResult(TechEffectResult):
    pass


@dataclass
class RemoveEffect(TechEffect):
    """
    This effect has a chance to remove a status effect.

    Parameters:
        condition: The Condition slug (e.g. enraged).
        objectives: The targets (e.g. own_monster, enemy_monster, etc.), if
            single "enemy_monster" or "enemy_monster:own_monster"

    eg "remove xxx,own_monster" removes only xxx
    eg "remove all,own_monster" removes everything
    """

    name = "remove"
    condition: str
    objectives: str

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> RemoveEffectResult:
        monsters: list[Monster] = []
        combat = tech.combat_state
        assert combat

        objectives = self.objectives.split(":")
        potency = random.random()
        value = combat._random_tech_hit.get(user, 0.0)
        success = tech.potency >= potency and tech.accuracy >= value

        if success:
            monsters = get_target_monsters(objectives, tech, user, target)
            if self.condition == "all":
                for monster in monsters:
                    monster.status.clear()
            else:
                for monster in monsters:
                    if has_status(monster, self.condition):
                        monster.status.clear()

        return {
            "success": bool(monsters),
            "damage": 0,
            "element_multiplier": 0.0,
            "should_tackle": False,
            "extra": None,
        }
