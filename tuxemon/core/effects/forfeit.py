# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.combat import set_var
from tuxemon.core.core_effect import CoreEffect, TechEffectResult
from tuxemon.db import OutputBattle
from tuxemon.locale import T

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.session import Session
    from tuxemon.states.combat.combat import CombatState
    from tuxemon.technique.technique import Technique


@dataclass
class ForfeitEffect(CoreEffect):
    """
    Forfeit allows player to forfeit.

    """

    name = "forfeit"

    def apply_tech_target(
        self, session: Session, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:
        combat = tech.combat_state
        player = user.owner
        assert combat and player
        set_var(session, "battle_last_result", self.name)
        set_var(session, "teleport_clinic", OutputBattle.lost.value)
        combat._run = True
        params = {"npc": combat.players[1].name.upper()}
        extra = [T.format("combat_forfeit", params)]
        self._clean_combat_state(combat)
        # Faint all player monsters
        for mon in player.monsters:
            mon.faint()

        return TechEffectResult(name=tech.name, success=True, extras=extra)

    def _clean_combat_state(self, combat: CombatState) -> None:
        """
        Clean up the combat state by removing all players and monsters.
        """
        for remove in combat.players:
            combat.clean_combat()
            del combat.monsters_in_play[remove]
            combat.players.remove(remove)
