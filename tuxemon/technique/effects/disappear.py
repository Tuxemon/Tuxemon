# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.states.combat.combat_classes import EnqueuedAction
from tuxemon.technique.techeffect import TechEffect, TechEffectResult
from tuxemon.technique.technique import Technique

if TYPE_CHECKING:
    from tuxemon.monster import Monster


class DisappearEffectResult(TechEffectResult):
    pass


@dataclass
class DisappearEffect(TechEffect):
    """
    Tuxemon disappears. It's followed by "appear".

    Parameters:
        attack: slug technique (attack when lands).
    """

    name = "disappear"
    attack: str

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> DisappearEffectResult:
        combat = tech.combat_state
        assert combat

        # Get the user's sprite
        user_sprite = combat._monster_sprite_map.get(user, None)
        if user_sprite and user_sprite.is_visible():
            # Make the user disappear
            user_sprite.toggle_visible()
            user.out_of_range = True
            # Create a new technique to land the user
            land_technique = Technique()
            land_technique.load(self.attack)
            # Add the land action to the pending queue
            land_action = EnqueuedAction(user, land_technique, target)
            combat._pending_queue.append(land_action)

        return {
            "success": user.out_of_range,
            "damage": 0,
            "element_multiplier": 0.0,
            "should_tackle": False,
            "extra": None,
        }
