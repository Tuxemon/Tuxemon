# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass

from tuxemon.monster import Monster
from tuxemon.technique.techeffect import TechEffect, TechEffectResult
from tuxemon.technique.technique import Technique


class SwapEffectResult(TechEffectResult):
    should_tackle: bool


@dataclass
class SwapEffect(TechEffect):
    """
    Used just for combat: change order of monsters.

    Position of monster in party will be changed.

    Returns:
        Dict summarizing the result.

    """

    name = "swap"
    objective: str

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> SwapEffectResult:
        # TODO: implement actions as events, so that combat state can find them
        # TODO: relies on setting "combat_state" attribute.  maybe clear it up
        # later
        # TODO: these values are set in combat_menus.py

        assert tech.combat_state
        # TODO: find a way to pass values. this will only work for SP games with one monster party
        combat_state = tech.combat_state

        def swap_add() -> None:
            # TODO: make accommodations for battlefield positions
            combat_state.add_monster_into_play(user, target)

        # get the original monster to be swapped out
        original_monster = combat_state.monsters_in_play[user][0]

        # rewrite actions to target the new monster.  must be done before original is removed
        combat_state.rewrite_action_queue_target(original_monster, target)

        # remove the old monster and all their actions
        combat_state.remove_monster_from_play(user, original_monster)

        # give a slight delay
        combat_state.task(swap_add, 0.75)
        combat_state.suppress_phase_change(0.75)

        return {"success": True, "should_tackle": False}
