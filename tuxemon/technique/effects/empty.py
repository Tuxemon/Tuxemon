# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.technique.techeffect import TechEffect, TechEffectResult

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.technique.technique import Technique


class EmptyEffectResult(TechEffectResult):
    pass


@dataclass
class EmptyEffect(TechEffect):
    """
    "This effect lets the technique show the animation, but it also prevents
    the technique from failing. Without it, the technique would automatically
    fail, because the effect list is empty [] and success is False by default.
    """

    name = "empty"

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> EmptyEffectResult:
        combat = tech.combat_state
        assert combat
        tech.hit = tech.accuracy >= combat._random_tech_hit.get(user, 0.0)
        return {
            "success": tech.hit,
            "damage": 0,
            "element_multiplier": 0.0,
            "should_tackle": False,
            "extra": None,
        }
