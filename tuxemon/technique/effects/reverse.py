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
        if self.objective not in ("user", "target", "both"):
            raise ValueError(
                f"{self.objective} must be 'user', 'target' or 'both'"
            )

        if self.objective in ["user", "both"]:
            user.reset_types()
        if self.objective in ["target", "both"]:
            target.reset_types()

        return {
            "success": True,
            "damage": 0,
            "element_multiplier": 0.0,
            "should_tackle": False,
            "extra": None,
        }
