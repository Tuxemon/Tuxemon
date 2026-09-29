# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon import formula
from tuxemon.combat.utils import set_var
from tuxemon.core.core_effect import CoreEffect, TechEffectResult
from tuxemon.locale.locale import T

if TYPE_CHECKING:
    from tuxemon.monster.monster import Monster
    from tuxemon.session import Session
    from tuxemon.technique.technique import Technique


@dataclass
class RunEffect(CoreEffect):
    """
    Applies the "run" effect to a technique.

    This effect represents a combat action where the monster attempts to
    flee from battle. The chance of success depends on the escape method,
    the number of previous attempts, and combat conditions.

    **Example**

    .. code-block:: json

        "effects": [
            "run"
        ]
    """

    name = "run"

    def apply_tech_target(
        self, session: Session, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:
        self.session = session
        self.combat_session = session.client.combat_session

        self.game_vars = session.player.game_variables
        attempts = self.game_vars.get("run_attempts", 0)
        escape_method = self._determine_escape_method(user)

        if not escape_method:
            return TechEffectResult(name=tech.name, success=True)

        success = formula.attempt_escape(escape_method, user, target, attempts)
        extras: list[str] = []

        if success:
            self._handle_successful_escape(extras)
        else:
            self.game_vars.set("run_attempts", attempts + 1)

        return TechEffectResult(name=tech.name, success=success, extras=extras)

    def _determine_escape_method(self, user: Monster) -> str | None:
        """
        Determines which escape method to use based on monster position.
        """
        method_player = str(self.game_vars.get("method_escape", "default"))
        method_ai = str(self.game_vars.get("method_escape_ai", "default"))

        if user in self.combat_session.monsters_in_play_right:
            return method_player
        elif user in self.combat_session.monsters_in_play_left:
            return method_ai
        return None

    def _handle_successful_escape(self, extras: list[str]) -> None:
        self.combat_session.set_variable("run", True)
        extras.append(T.translate("combat_player_run"))
        self.game_vars.set("run_attempts", 0)
        set_var(self.session, "battle_last_result", self.name)

        self._clean_combat_state()

    def _clean_combat_state(self) -> None:
        event_bus = self.session.client.event_bus
        event_bus.publish("clean_combat")

        for player in self.combat_session.players:
            self.combat_session.field_monsters.remove_npc(player)
            self.combat_session.remove_player(player)

        self.combat_session.reset()
