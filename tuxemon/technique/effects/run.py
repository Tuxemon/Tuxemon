# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from tuxemon import formula
from tuxemon.combat import set_var
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
        combat = tech.combat_state
        player = user.owner
        assert combat and player

        game_variables = player.game_variables
        attempts = game_variables.get("run_attempts", 0)
        escape_method = game_variables.get("method_escape", "default")
        escape_ai_method = game_variables.get("method_escape_ai", "default")

        # Check if the user is in the player party or NPC party
        if user in combat.monsters_in_play_right:
            escape_method = escape_method
        elif user in combat.monsters_in_play_left:
            escape_method = escape_ai_method
        else:
            return {
                "success": True,
                "damage": 0,
                "element_multiplier": 0.0,
                "should_tackle": False,
                "extra": None,
            }

        # Attempt to escape
        if formula.attempt_escape(
            escape_method,
            user,
            target,
            attempts,
        ):
            game_variables["run_attempts"] = 0
            ran = True

        # Trigger the run effect
        if ran:
            combat._run = True
            extra = T.translate("combat_player_run")
            set_var(self.session, "battle_last_result", self.name)
            for remove in combat.players:
                combat.clean_combat()
                del combat.monsters_in_play[remove]
                combat.players.remove(remove)
        else:
            game_variables["run_attempts"] = attempts + 1

        return {
            "success": ran,
            "damage": 0,
            "element_multiplier": 0.0,
            "should_tackle": False,
            "extra": extra,
        }
