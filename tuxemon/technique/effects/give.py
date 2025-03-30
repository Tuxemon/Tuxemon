# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.combat import get_target_monsters
from tuxemon.status.status import Status
from tuxemon.technique.techeffect import TechEffect, TechEffectResult
from tuxemon.technique.technique import Technique

if TYPE_CHECKING:
    from tuxemon.monster import Monster


@dataclass
class GiveEffect(TechEffect):
    """
    This effect has a chance to give a status effect.

    Parameters:
        condition: The Status slug (e.g. enraged).
        objectives: The targets (e.g. own_monster, enemy_monster, etc.), if
            single "enemy_monster" or "enemy_monster:own_monster"

    eg "give enraged,own_monster"
    """

    name = "give"
    condition: str
    objectives: str

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:
        monsters: list[Monster] = []
        combat = tech.combat_state
        player = user.owner
        assert combat and player

        objectives = self.objectives.split(":")
        potency = random.random()
        value = combat._random_tech_hit.get(user, 0.0)
        success = tech.potency >= potency and tech.accuracy >= value

        if success:
            status = Status()
            status.load(self.condition)
            status.steps = player.steps
            status.link = user

            monsters = get_target_monsters(objectives, tech, user, target)
            if monsters:
                for monster in monsters:
                    monster.apply_status(status)
                combat.reset_status_icons()

        return TechEffectResult(
            name=tech.name,
            success=bool(monsters),
            damage=0,
            element_multiplier=0.0,
            should_tackle=False,
            extras=[],
        )
