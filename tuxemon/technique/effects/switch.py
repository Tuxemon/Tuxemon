# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.db import ElementType
from tuxemon.element import Element
from tuxemon.locale import T
from tuxemon.technique.techeffect import TechEffect, TechEffectResult

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.technique.technique import Technique


class SwitchEffectResult(TechEffectResult):
    pass


@dataclass
class SwitchEffect(TechEffect):
    """
    Changes monster type.
    "switch user,wood"
    "switch target,fire"
    "switch both,random"
    if "switch target,random"
    then the type is chosen randomly.

    """

    name = "switch"
    objective: str
    element: str

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> SwitchEffectResult:
        if self.objective not in ("user", "target", "both"):
            raise ValueError(
                f"{self.objective} must be 'user', 'target' or 'both'"
            )

        elements = list(ElementType)

        if self.element == "random":
            user_element = Element(random.choice(elements))
            target_element = Element(random.choice(elements))
        else:
            user_element = Element(self.element)
            target_element = Element(self.element)

        extra = None
        if self.objective == "both":
            if user.has_type(user_element.slug):
                extra = get_failure_message(user, user_element)
            elif target.has_type(target_element.slug):
                extra = get_failure_message(target, target_element)
            else:
                user.types = [user_element]
                target.types = [target_element]
                extra = get_extra_message_both(user, target, user_element)
        else:
            monster = "user" if self.objective == "user" else "target"
            monster_element = (
                user_element if monster == "user" else target_element
            )
            if (monster == "user" and user.has_type(monster_element.slug)) or (
                monster == "target" and target.has_type(monster_element.slug)
            ):
                extra = get_failure_message(
                    (user if monster == "user" else target), monster_element
                )
            else:
                if monster == "user":
                    user.types = [monster_element]
                else:
                    target.types = [monster_element]
                extra = get_failure_message(
                    (user if monster == "user" else target), monster_element
                )

        return {
            "success": True,
            "damage": 0,
            "element_multiplier": 0.0,
            "should_tackle": False,
            "extra": extra,
        }


def get_extra_message_both(
    user: Monster, target: Monster, new_type: Element
) -> str:
    params = {
        "user": user.name.upper(),
        "type1": T.translate(new_type.slug).upper(),
        "target": target.name.upper(),
        "type2": T.translate(new_type.slug).upper(),
    }
    return T.format("combat_state_switch_both", params)


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
