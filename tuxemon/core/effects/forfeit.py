# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.combat.utils import set_var
from tuxemon.core.core_effect import CoreEffect, TechEffectResult
from tuxemon.locale.locale import T

if TYPE_CHECKING:
    from tuxemon.entity.npc import NPC
    from tuxemon.monster.monster import Monster
    from tuxemon.session import Session
    from tuxemon.technique.technique import Technique


@dataclass
class ForfeitEffect(CoreEffect):
    """
    Applies the "forfeit" effect in combat.

    This effect represents surrendering a battle. When triggered, it ends the
    combat session, faints all monsters belonging to the forfeiting player,
    and records the outcome as a forfeit.

    **Example**

    .. code-block:: json

        "effects": [
            "forfeit"
        ]
    """

    name = "forfeit"

    def apply_tech_target(
        self, session: Session, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:
        self.client = session.client
        player = user.get_owner()

        set_var(session, "battle_last_result", self.name)
        self.client.combat_session.set_variable("run", True)

        params = {"npc": self.client.combat_session.right_player.name.upper()}
        extras = [T.format("combat_forfeit", params)]

        self._clean_combat_state()
        self._faint_all_monsters(player)

        return TechEffectResult(name=tech.name, success=True, extras=extras)

    def _clean_combat_state(self) -> None:
        event_bus = self.client.event_bus
        event_bus.publish("clean_combat")

        combat_session = self.client.combat_session
        for player in combat_session.players:
            combat_session.field_monsters.remove_npc(player)
            combat_session.remove_player(player)

        combat_session.reset()

    def _faint_all_monsters(self, char: NPC) -> None:
        for monster in char.monsters:
            monster.current_hp = 0
