# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.locale import T
from tuxemon.states.combat.combat import EnqueuedAction
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
        done = True
        combat = tech.combat_state
        assert combat

        # make fly the user
        user_sprite = combat._monster_sprite_map.get(user, None)
        if user_sprite and user_sprite.visible:
            user_sprite.visible = False
            user.out_of_range = True
            technique = Technique()
            technique.load(self.attack)
            land = EnqueuedAction(user, technique, target)
            combat._pending_queue.append(land)
        else:
            # if it's already flying
            done = False

        extra = T.format(
            "combat_fly",
            {
                "name": user.name.upper(),
            },
        )

        return {
            "success": done,
            "damage": 0,
            "element_multiplier": 0.0,
            "should_tackle": False,
            "extra": extra,
        }
