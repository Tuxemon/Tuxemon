# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from tuxemon.db import OutputBattle
from tuxemon.locale import T
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
        extra: Optional[str] = None
        ran: bool = False
        if tech.combat_state is None or user.owner is None:
            raise ValueError()
        combat = tech.combat_state

        def escape(level_user: int, level_target: int, attempts: int) -> bool:
            escaping: bool = False
            escape = 0.4 + (0.15 * (attempts + level_user - level_target))
            if random.random() <= escape:
                escaping = True
            return escaping

        var = user.owner.game_variables
        if "run_attempts" not in var:
            var["run_attempts"] = 0
        # monster in the player party
        if user in combat.monsters_in_play_human:
            if escape(user.level, target.level, var["run_attempts"]):
                var["run_attempts"] += 1
                ran = True
        # monster in the NPC party
        elif user in combat.monsters_in_play_ai:
            ran = True

        # trigger run
        if ran:
            combat._run = True
            extra = T.translate("combat_player_run")
            var["battle_last_result"] = OutputBattle.ran
            for remove in combat.players:
                combat.clean_combat()
                del combat.monsters_in_play[remove]
                combat.players.remove(remove)

        return {
            "success": ran,
            "damage": 0,
            "element_multiplier": 0.0,
            "should_tackle": False,
            "extra": extra,
        }
