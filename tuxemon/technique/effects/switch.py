# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

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

    """

    name = "switch"
    objective: str
    element: str

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> SwitchEffectResult:
        elements = list(ElementType)
        if self.element in elements:
            ele = ElementType(self.element)
            if ele not in target.types:
                if self.objective == "user":
                    user.types = [ele]
                    return {"success": True}
                elif self.objective == "target":
                    target.types = [ele]
                    return {"success": True}
                else:
                    return {"success": False}
            else:
                return {"success": False}
        else:
            return {"success": False}
