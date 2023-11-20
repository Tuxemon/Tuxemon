# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.technique.techeffect import TechEffect, TechEffectResult

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.technique.technique import Technique


class MultiAttackEffectResult(TechEffectResult):
    pass


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
    ) -> MultiAttackEffectResult:
        player = self.session.player
        value = random.random()
        player.game_variables["random_tech_hit"] = value
        done: bool = True
        _track: int = 0
        assert tech.combat_state
        combat = tech.combat_state
        log = combat._log_action
        turn = combat._turn
        track = [
            action
            for action in log
            if turn == action[0]
            and action[1].method == tech
            and action[1].user == user
            and action[1].target == target
        ]
        if track:
            _track = len(track)

        if _track == self.times:
            done = False

        # check if technique hits
        hit = tech.accuracy >= value

        if done and hit:
            combat.enqueue_action(user, tech, target)

        return {
            "damage": 0,
            "element_multiplier": 0.0,
            "should_tackle": bool(done),
            "success": bool(done),
            "extra": None,
        }
