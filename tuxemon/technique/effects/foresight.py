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
class ForesightEffect(TechEffect):
    """
    The ForesightEffect allows you to set a future turn where the associated technique
    will be reused with its power set to the specified number of turns. This effect
    can be used to plan ahead and execute a technique with a guaranteed increased power.

    The technique will be reused after the specified number of turns have passed,
    regardless of other events that may occur.

    Parameters:
        turn: number of turns after which the technique will be reused.

    Example:
        If the current turn is 5 and self.turn is 3, the technique will be reused
        on turn 8 (5 + 3) with a power of 3.0.
    """

    name = "foresight"
    turn: int

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:

        if self.turn <= 0:
            raise ValueError(f"{self.turn} cannot be 0 or negative")

        combat = tech.combat_state
        assert combat

        set_technique = Technique()
        set_technique.load(tech.slug)
        set_technique.power = self.turn

        next_turn = combat._turn + self.turn
        action = EnqueuedAction(user, set_technique, target)
        combat._action_queue.add_pending(action, next_turn)

        return TechEffectResult(
            name=tech.name,
            success=True,
            damage=0,
            element_multiplier=0.0,
            should_tackle=False,
            extras=[],
        )
