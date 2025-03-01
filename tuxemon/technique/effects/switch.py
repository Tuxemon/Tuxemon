# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.combat import get_target_monsters
from tuxemon.db import db
from tuxemon.element import Element
from tuxemon.locale import T
from tuxemon.technique.techeffect import TechEffect, TechEffectResult

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.technique.technique import Technique


@dataclass
class SwitchEffect(TechEffect):
    """
    Changes monster type.

    Parameters:
        objectives: The targets (e.g. own_monster, enemy_monster, etc.), if
            single "enemy_monster" or "enemy_monster:own_monster"
        element: The element (e.g. wood, fire, etc.) or random.

    eg switch enemy_monster,wood
    eg switch enemy_monster:own_monster,fire
    eg switch own_monster,random
    """

    name = "switch"
    objectives: str
    element: str

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:

        elements = list(db.database["element"])
        combat = tech.combat_state
        assert combat

        tech.hit = tech.accuracy >= combat._random_tech_hit.get(user, 0.0)

        if not tech.hit:
            return TechEffectResult(
                name=tech.name,
                success=tech.hit,
                damage=0,
                element_multiplier=0.0,
                should_tackle=False,
                extras=[],
            )

        objectives = self.objectives.split(":")
        monsters = get_target_monsters(objectives, tech, user, target)

        if self.element == "random":
            new_type = Element(random.choice(elements))
        else:
            new_type = Element(self.element)

        messages = []
        for monster in monsters:
            if monster.has_type(new_type.slug):
                messages.append(get_failure_message(monster, new_type))
            else:
                monster.types = [new_type]
                messages.append(get_extra_message(monster, new_type))

        extra = ["\n".join(messages)]
        return TechEffectResult(
            name=tech.name,
            success=tech.hit,
            damage=0,
            element_multiplier=0.0,
            should_tackle=False,
            extras=extra,
        )


def get_extra_message(monster: Monster, new_type: Element) -> str:
    params = {
        "target": monster.name.upper(),
        "types": T.translate(new_type.slug).upper(),
    }
    return T.format("combat_state_switch", params)


def get_failure_message(monster: Monster, new_type: Element) -> str:
    params = {
        "target": monster.name.upper(),
        "type": T.translate(new_type.slug).upper(),
    }
    return T.format("combat_state_switch_fail", params)
