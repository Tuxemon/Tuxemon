# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.technique.techeffect import TechEffect, TechEffectResult

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.technique.technique import Technique


@dataclass
class MultiAttackEffect(TechEffect):
    """
    Multiattack #: Do # attacks.

    Parameters:
        times: how many times multiattack

    eg effects ["multiattack 3", "damage"]

    """

    name = "multiattack"
    times: int

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:
        assert tech.combat_state
        combat = tech.combat_state
        value = random.random()
        combat._random_tech_hit[user] = value
        # Track previous actions with the same technique, user, and target
        log = combat._action_queue.history.get_actions_by_turn(combat._turn)
        track = [
            action
            for action in log
            if action.method == tech
            and action.user == user
            and action.target == target
        ]
        # Check if the technique has been used the maximum number of times
        done = len(track) < self.times
        # Check if the technique hits
        hit = tech.accuracy >= value
        # If the technique is done and hits, enqueue the action
        if done and hit:
            combat.enqueue_action(user, tech, target)

        return TechEffectResult(
            name=tech.name,
            damage=0,
            element_multiplier=0.0,
            should_tackle=done,
            success=done,
            extras=[],
        )
