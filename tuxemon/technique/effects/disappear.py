# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.states.combat.combat_classes import EnqueuedAction
from tuxemon.technique.techeffect import TechEffect, TechEffectResult
from tuxemon.technique.technique import Technique

if TYPE_CHECKING:
    from tuxemon.monster import Monster


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
    ) -> TechEffectResult:
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
            combat._action_queue.add_pending(land_action, combat._turn)

        return TechEffectResult(
            name=tech.name,
            success=user.out_of_range,
            damage=0,
            element_multiplier=0.0,
            should_tackle=False,
            extras=[],
        )
