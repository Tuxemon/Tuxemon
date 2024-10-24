# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.combat import get_target_monsters
from tuxemon.condition.condition import Condition
from tuxemon.technique.techeffect import TechEffect, TechEffectResult
from tuxemon.technique.technique import Technique

if TYPE_CHECKING:
    from tuxemon.monster import Monster


class GiveEffectResult(TechEffectResult):
    pass


@dataclass
class GiveEffect(TechEffect):
    """
    This effect has a chance to give a status effect.

    Parameters:
        condition: The Condition slug (e.g. enraged).
        objectives: The targets (e.g. own_monster, enemy_monster, etc.), if
            single "enemy_monster" or "enemy_monster:own_monster"

    eg "give enraged,own_monster"
    """

    name = "give"
    condition: str
    objectives: str

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> GiveEffectResult:
        monsters: list[Monster] = []
        combat = tech.combat_state
        player = user.owner
        assert combat and player

        objectives = self.objectives.split(":")
        potency = random.random()
        value = combat._random_tech_hit.get(user, 0.0)
        success = tech.potency >= potency and tech.accuracy >= value

        if success:
            status = Condition()
            status.load(self.condition)
            status.steps = player.steps

            monsters = get_target_monsters(objectives, tech, user, target)
            if monsters:
                for monster in monsters:
                    status.link = monster
                    monster.apply_status(status)
                combat.reset_status_icons()

        return {
            "success": bool(monsters),
            "damage": 0,
            "element_multiplier": 0.0,
            "should_tackle": False,
            "extra": None,
        }
