from __future__ import annotations

from typing import NamedTuple

from tuxemon.monster import Monster
from tuxemon.technique.techeffect import TechEffect, TechEffectResult


class SwapEffectResult(TechEffectResult):
    should_tackle: bool


class SwapEffectParameters(NamedTuple):
    pass


class SwapEffect(TechEffect[SwapEffectParameters]):
    """
    Used just for combat: change order of monsters.

    Position of monster in party will be changed.

    Returns:
        Dict summarizing the result.

    """

    name = "swap"
    param_class = SwapEffectParameters

    def apply(self, user: Monster, target: Monster) -> SwapEffectResult:
        # TODO: implement actions as events, so that combat state can find them
        # TODO: relies on setting "combat_state" attribute.  maybe clear it up
        # later
        # TODO: these values are set in combat_menus.py

        assert self.move.combat_state
        # TODO: find a way to pass values. this will only work for SP games with one monster party
        combat_state = self.move.combat_state

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
