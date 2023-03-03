# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass

from tuxemon.monster import Monster
from tuxemon.technique.techeffect import TechEffect, TechEffectResult
from tuxemon.technique.technique import Technique


@dataclass
class EnhanceEffect(TechEffect):
    """
    Apply "damage" for special range. Allows to show the animation and
    avoids a constant failure.

    Parameters:
        user: The Monster object that used this technique.
        target: The Monster object that we are using this technique on.

    Returns:
        Dict summarizing the result.

    """

    name = "enhance"

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:
        player = self.session.player
        value = float(player.game_variables["random_tech_hit"])
        hit = tech.accuracy >= value
        if hit or tech.is_area:
            return {
                "damage": 0,
                "should_tackle": True,
                "success": True,
                "element_multiplier": 0,
            }
        else:
            return {
                "damage": 0,
                "should_tackle": False,
                "success": False,
                "element_multiplier": 0,
            }
