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


class RunEffectResult(TechEffectResult):
    pass


@dataclass
class RunEffect(TechEffect):
    """
    Run allows monster to run.

    """

    name = "run"

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> RunEffectResult:
        ran: bool = False
        combat = tech.combat_state
        assert combat

        def escape(level_user: int, level_target: int, attempts: int) -> bool:
            escaping: bool = False
            escape = 0.4 + (0.15 * (attempts + level_user - level_target))
            if random.random() <= escape:
                escaping = True
            return escaping

        var = self.session.player.game_variables
        if user in combat.monsters_in_play_human:
            if "run_attempts" not in var:
                var["run_attempts"] = 0
            if escape(user.level, target.level, var["run_attempts"]):
                var["run_attempts"] += 1
                ran = True
        elif user in combat.monsters_in_play_ai:
            ran = True

        return {"success": ran}
