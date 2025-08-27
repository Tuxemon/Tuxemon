# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, TechEffectResult

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.session import Session
    from tuxemon.technique.technique import Technique


@dataclass
class MultiAttackEffect(CoreEffect):
    """
    Multiattack #: Do # attacks.

    Parameters:
        times: how many times multiattack

    eg effects ["multiattack 3", "damage"]

    """

    name = "multiattack"
    times: int

    def apply_tech_target(
        self, session: Session, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:
        combat_session = session.client.combat_session
        combat_session.set_tech_hit(user)
        # Track previous actions with the same technique, user, and target
        turn = combat_session.turn
        action_queue = combat_session.action_queue
        log = action_queue.history.get_actions_by_turn(turn)
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
        hit = tech.accuracy >= combat_session.get_tech_hit(user)
        # If the technique is done and hits, enqueue the action
        if done and hit:
            combat_session.enqueue_action(user, tech, target)

        return TechEffectResult(
            name=tech.name, should_tackle=done, success=done
        )
