# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

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
        extra: Optional[str] = None
        done: bool = False
        elements = list(ElementType)
        if self.element != "random":
            ele = Element(self.element)
            if ele not in target.types:
                if self.objective == "user":
                    user.types = [ele]
                    done = True
                elif self.objective == "target":
                    target.types = [ele]
                    done = True
                elif self.objective == "both":
                    user.types = [ele]
                    target.types = [ele]
                    done = True
        else:
            _user = random.choice(elements)
            _target = random.choice(elements)
            ele_u = Element(_user)
            ele_t = Element(_target)
            if self.objective == "user":
                user.types = [ele_u]
                done = True
            elif self.objective == "target":
                target.types = [ele_t]
                done = True
            elif self.objective == "both":
                user.types = [ele_u]
                target.types = [ele_t]
                done = True
        if done:
            _type: str = ""
            _monster: str = ""
            if self.objective == "both":
                extra = T.format(
                    "combat_state_switch_both",
                    {
                        "user": user.name.upper(),
                        "type1": T.translate(user.types[0].slug),
                        "target": target.name.upper(),
                        "type2": T.translate(target.types[0].slug),
                    },
                )
            else:
                if self.objective == "target":
                    _monster = target.name.upper()
                    _type = T.translate(target.types[0].slug)
                if self.objective == "user":
                    _monster = user.name.upper()
                    _type = T.translate(user.types[0].slug)
                extra = T.format(
                    "combat_state_switch",
                    {
                        "target": _monster,
                        "types": _type,
                    },
                )
        return {
            "success": done,
            "damage": 0,
            "element_multiplier": 0.0,
            "should_tackle": False,
            "extra": extra,
        }
