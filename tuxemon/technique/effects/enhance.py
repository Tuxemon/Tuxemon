# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.technique.techeffect import TechEffect, TechEffectResult

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.technique.technique import Technique


class EnhanceEffectResult(TechEffectResult):
    pass


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
    ) -> EnhanceEffectResult:
        player = self.session.player
        value = float(player.game_variables["random_tech_hit"])
        hit = tech.accuracy >= value
        if hit or tech.is_area:
            tech.advance_counter_success()
            return {"success": True}
        else:
            return {"success": False}
