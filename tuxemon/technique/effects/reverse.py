# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.technique.techeffect import TechEffect, TechEffectResult

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.technique.technique import Technique


class ReverseEffectResult(TechEffectResult):
    pass


@dataclass
class ReverseEffect(TechEffect):
    """
    Reverse "Switch" effect:
    it returns the original monster type.
    "reverse user"
    "reverse target"
    "reverse both"
    """

    name = "reverse"
    objective: str

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> ReverseEffectResult:
        done: bool = False
        if self.objective == "user":
            user.reset_types()
            done = True
        elif self.objective == "target":
            target.reset_types()
            done = True
        elif self.objective == "both":
            user.reset_types()
            target.reset_types()
            done = True
        return {
            "success": done,
            "damage": 0,
            "element_multiplier": 0.0,
            "should_tackle": False,
            "extra": None,
        }
