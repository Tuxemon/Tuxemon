# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from functools import partial
from typing import TYPE_CHECKING

from tuxemon.technique.techeffect import TechEffect, TechEffectResult

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.technique.technique import Technique


@dataclass
class SwapEffect(TechEffect):
    """
    Used just for combat: change order of monsters.

    Position of monster in party will be changed.

    Returns:
        Dict summarizing the result.

    """

    name = "swap"

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:
        # TODO: implement actions as events, so that combat state can find them
        # TODO: relies on setting "combat_state" attribute.  maybe clear it up
        # later
        # TODO: these values are set in combat_menus.py
        assert tech.combat_state and user.owner
        player = user.owner
        combat_state = tech.combat_state

        def swap_add(removed: Monster) -> None:
            # TODO: make accommodations for battlefield positions
            combat_state.add_monster_into_play(player, target, removed)

        # rewrite actions to target the new monster.  must be done before original is removed
        combat_state._action_queue.swap(user, target)

        # remove the old monster and all their actions
        combat_state.remove_monster_from_play(user)

        # give a slight delay
        combat_state.task(partial(swap_add, user), 0.75)

        return TechEffectResult(
            name=tech.name,
            success=True,
            damage=0,
            element_multiplier=0.0,
            should_tackle=False,
            extras=[],
        )
