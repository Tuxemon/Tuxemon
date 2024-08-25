# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.locale import T
from tuxemon.states.combat.combat_classes import EnqueuedAction
from tuxemon.technique.techeffect import TechEffect, TechEffectResult
from tuxemon.technique.technique import Technique

if TYPE_CHECKING:
    from tuxemon.monster import Monster


class FlyOffEffectResult(TechEffectResult):
    pass


@dataclass
class FlyOffEffect(TechEffect):
    """
    Tuxemon flies off.

    Parameters:
        attack: slug technique (attack when lands).

    """

    name = "fly_off"
    attack: str

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> FlyOffEffectResult:
        user_is_flying = False
        combat = tech.combat_state
        assert combat

        # Get the user's sprite
        user_sprite = combat._monster_sprite_map.get(user, None)
        if user_sprite and user_sprite.visible:
            # Make the user fly
            user_sprite.visible = False
            user.out_of_range = True
            # Create a new technique to land the user
            land_technique = Technique()
            land_technique.load(self.attack)
            # Add the land action to the pending queue
            land_action = EnqueuedAction(user, land_technique, target)
            combat._pending_queue.append(land_action)
        else:
            # If the user is already flying, don't do anything
            user_is_flying = True

        params = {"name": user.name.upper()}
        extra = T.format("combat_fly", params)

        return {
            "success": not user_is_flying,
            "damage": 0,
            "element_multiplier": 0.0,
            "should_tackle": False,
            "extra": extra,
        }
