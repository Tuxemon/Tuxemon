# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
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
        done = True
        combat = tech.combat_state
        assert combat

        # make land the user
        user_sprite = combat._monster_sprite_map.get(user, None)
        assert user_sprite
        if not user_sprite.visible:
            user_sprite.visible = True
            user.out_of_range = False

        # check if the enemy isn't flying
        target_sprite = combat._monster_sprite_map.get(target, None)
        assert target_sprite
        if not target_sprite.visible:
            done = False

        return {
            "success": done,
            "damage": 0,
            "element_multiplier": 0.0,
            "should_tackle": done,
            "extra": None,
        }
