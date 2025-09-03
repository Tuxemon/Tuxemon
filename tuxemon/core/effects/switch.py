# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, TechEffectResult
from tuxemon.db import db
from tuxemon.element import Element
from tuxemon.locale import T

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.session import Session
    from tuxemon.technique.technique import Technique


@dataclass
class SwitchEffect(CoreEffect):
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

    def apply_tech_target(
        self, session: Session, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:

        elements = list(db.database["element"])
        hit = session.client.combat_session.get_tech_hit(user)

        tech.hit = tech.accuracy >= hit

        if not tech.hit:
            return TechEffectResult(name=tech.name, success=tech.hit)

        objectives = self.objectives.split(":")
        monsters = session.client.combat_session.get_target_monsters(
            objectives, user, target
        )

        if self.element == "random":
            new_type = Element(random.choice(elements))
        else:
            new_type = Element(self.element)

        messages = []
        for monster in monsters:
            if monster.has_type(new_type.slug):
                messages.append(get_failure_message(monster, new_type))
            else:
                monster.types.set_types([new_type])
                messages.append(get_extra_message(monster, new_type))

        extra = ["\n".join(messages)]
        return TechEffectResult(name=tech.name, success=tech.hit, extras=extra)


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
