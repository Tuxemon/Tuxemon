# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.technique.techeffect import TechEffect, TechEffectResult

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.technique.technique import Technique


class LandEffectResult(TechEffectResult):
    pass


@dataclass
class LandEffect(TechEffect):
    """
    Tuxemon lands.

    """

    name = "land"

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> LandEffectResult:
        combat = tech.combat_state
        assert combat
        # Check if the user is flying
        user_sprite = combat._monster_sprite_map.get(user, None)
        if user_sprite and not user_sprite.visible:
            # Make the user land
            user_sprite.visible = True
            user.out_of_range = False

        # Check if the target is flying
        target_sprite = combat._monster_sprite_map.get(target, None)
        if target_sprite and not target_sprite.visible:
            # If the target is flying, don't tackle
            target_is_flying = True
        else:
            target_is_flying = False

        # Return the result
        return {
            "success": not target_is_flying,
            "damage": 0,
            "element_multiplier": 0.0,
            "should_tackle": not target_is_flying,
            "extra": None,
        }
