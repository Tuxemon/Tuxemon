# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional

from tuxemon import formula
from tuxemon.combat import set_var
from tuxemon.locale import T
from tuxemon.technique.techeffect import TechEffect, TechEffectResult

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.npc import NPC
    from tuxemon.states.combat.combat import CombatState
    from tuxemon.technique.technique import Technique


@dataclass
class RunEffect(TechEffect):
    """
    Run allows monster to run.

    """

    name = "run"

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:
        extra: list[str] = []
        ran: bool = False
        combat = tech.combat_state
        player = user.owner
        assert combat and player

        game_variables = player.game_variables
        attempts = game_variables.get("run_attempts", 0)

        method = self._determine_escape_method(user, combat, game_variables)
        if not method:
            return self._default_result(tech)

        if formula.attempt_escape(method, user, target, attempts):
            self._trigger_escape(combat, player, game_variables, extra)
            ran = True
        else:
            game_variables["run_attempts"] = attempts + 1

        return TechEffectResult(
            name=tech.name,
            success=ran,
            damage=0,
            element_multiplier=0.0,
            should_tackle=False,
            extras=extra,
        )

    def _determine_escape_method(
        self,
        user: Monster,
        combat: CombatState,
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
        player: NPC,
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

    def _default_result(self, tech: Technique) -> TechEffectResult:
        """
        Return the default result for the RunEffect.
        """
        return TechEffectResult(
            name=tech.name,
            success=True,
            damage=0,
            element_multiplier=0.0,
            should_tackle=False,
            extras=[],
        )
