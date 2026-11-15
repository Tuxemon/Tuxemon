# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, TechEffectResult
from tuxemon.database.runtime import db
from tuxemon.locale.locale import T

if TYPE_CHECKING:
    from tuxemon.monster.monster import Monster
    from tuxemon.session import Session
    from tuxemon.technique.technique import Technique


@dataclass
class SwitchEffect(CoreEffect):
    """
    Applies the "switch" effect to a technique.

    This effect changes the elemental type(s) of one or more target monsters.
    It can assign a specific element or select one randomly from the database.
    If the monster already has the specified type, the effect fails gracefully
    with a localized failure message.

    **Parameters**

    - ``objectives``: Colon-separated string specifying which monsters are
      affected. Examples:
      - ``enemy_monster`` → changes only the enemy's type.
      - ``own_monster`` → changes only the user's type.
      - ``enemy_monster:own_monster`` → changes both the enemy's and the user's type.
    - ``element``: The new element to assign.
      - Can be a specific element (e.g., ``fire``, ``wood``).
      - Or ``random`` to select a random element from the database.

    **Example**

    .. code-block:: json

        "effects": [
            "switch enemy_monster,wood"
        ]

        "effects": [
            "switch enemy_monster:own_monster,fire"
        ]

        "effects": [
            "switch own_monster,random"
        ]
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
            return TechEffectResult(name=tech.name, success=False)

        objectives = self.objectives.split(":")
        monsters = session.client.combat_session.get_target_monsters(
            objectives, user, target
        )

        if self.element == "random":
            new_slug = random.choice(elements)
        else:
            new_slug = self.element

        messages = []
        for monster in monsters:
            if monster.has_type(new_slug):
                messages.append(get_failure_message(monster, new_slug))
            else:
                monster.types.set_types([new_slug])
                messages.append(get_extra_message(monster, new_slug))

        extra = ["\n".join(messages)]
        return TechEffectResult(name=tech.name, success=True, extras=extra)


def get_extra_message(monster: Monster, slug: str) -> str:
    params = {
        "target": monster.name.upper(),
        "types": T.translate(slug).upper(),
    }
    return T.format("combat_state_switch", params)


def get_failure_message(monster: Monster, slug: str) -> str:
    params = {
        "target": monster.name.upper(),
        "type": T.translate(slug).upper(),
    }
    return T.format("combat_state_switch_fail", params)
