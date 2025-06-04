# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional

from tuxemon import formula
from tuxemon.combat import set_var
from tuxemon.core.core_effect import CoreEffect, TechEffectResult
from tuxemon.locale import T

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.session import Session
    from tuxemon.states.combat.combat import CombatState
    from tuxemon.technique.technique import Technique


@dataclass
class RunEffect(CoreEffect):
    """Run allows monster to run."""

    name = "run"

    def apply_tech_target(
        self, session: Session, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:
        extra: list[str] = []
        ran: bool = False
        combat = tech.combat_state
        self.player = user.owner
        self.session = session
        assert combat and self.player

        game_variables = self.player.game_variables
        attempts = game_variables.get("run_attempts", 0)

        method = self._determine_escape_method(combat, user, game_variables)
        if not method:
            return TechEffectResult(name=tech.name, success=True)

        if formula.attempt_escape(method, user, target, attempts):
            self._trigger_escape(combat, game_variables, extra)
            ran = True
        else:
            game_variables["run_attempts"] = attempts + 1

        return TechEffectResult(name=tech.name, success=ran, extras=extra)

    def _determine_escape_method(
        self,
        combat: CombatState,
        user: Monster,
        game_variables: dict[str, Any],
    ) -> Optional[str]:
        """
        Determine the appropriate escape method based on combat state.
        """
        escape_method = str(game_variables.get("method_escape", "default"))
        escape_ai_method = str(
            game_variables.get("method_escape_ai", "default")
        )

        if user in combat.monsters_in_play_right:
            return escape_method
        elif user in combat.monsters_in_play_left:
            return escape_ai_method
        else:
            return None

    def _trigger_escape(
        self,
        combat: CombatState,
        game_variables: dict[str, Any],
        extra: list[str],
    ) -> None:
        """
        Handle the escape trigger and clean up the combat state.
        """
        combat._run = True
        extra.append(T.translate("combat_player_run"))
        game_variables["run_attempts"] = 0
        set_var(self.session, "battle_last_result", self.name)

        # Clean up combat for all players
        players_to_remove = list(combat.players)
        for player in players_to_remove:
            combat.clean_combat()
            del combat.monsters_in_play[player]
            combat.players.remove(player)
