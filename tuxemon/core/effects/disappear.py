# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, TechEffectResult
from tuxemon.states.combat.combat_classes import EnqueuedAction
from tuxemon.technique.technique import Technique

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.session import Session


@dataclass
class DisappearEffect(CoreEffect):
    """
    Tuxemon disappears. It's followed by "appear".

    Parameters:
        attack: slug technique (attack when lands).
    """

    name = "disappear"
    attack: str

    def apply_tech_target(
        self, session: Session, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:
        combat = tech.combat_state
        assert combat

        # Get the user's sprite
        user_sprite = combat.sprite_map.get_sprite(user)
        if user_sprite and user_sprite.is_visible():
            # Make the user disappear
            user_sprite.toggle_visible()
            user.out_of_range = True
            # Create a new technique to land the user
            land_technique = Technique.create(self.attack)
            # Add the land action to the pending queue
            land_action = EnqueuedAction(user, land_technique, target)
            combat._action_queue.add_pending(land_action, combat._turn)

        return TechEffectResult(name=tech.name, success=user.out_of_range)
