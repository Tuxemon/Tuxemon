# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.db import ElementType
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
        done: bool = False
        elements = list(ElementType)
        if self.element in elements:
            ele = ElementType(self.element)
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
        if self.element == "random":
            _user = random.choice(elements)
            _target = random.choice(elements)
            if self.objective == "user":
                user.types = [_user]
                done = True
            elif self.objective == "target":
                target.types = [_target]
                done = True
            elif self.objective == "both":
                user.types = [_user]
                target.types = [_target]
                done = True
        return {"success": done}
