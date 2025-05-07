# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction

logger = logging.getLogger(__name__)


@final
@dataclass
class SetPartyStatusAction(EventAction):
    """
    Records important information about all monsters in the party.

    Script usage:
        .. code-block::

            set_party_status <player>

    Script parameters:
        character: Either "player" or npc slug name (e.g. "npc_maple").
    """

    name = "set_party_status"
    character: str

    def start(self) -> None:
        char = get_npc(self.session, self.character)
        if char is None:
            logger.error(f"{self.character} not found")
            return
        if not char.monsters:
            logger.error(f"{char.name} has no monsters!")
            return

        _healthy = sum(
            1 for monster in char.monsters if monster.hp_ratio == 1.0
        )
        _lost_hp = sum(monster.missing_hp for monster in char.monsters)
        party_healthy = "yes" if _healthy == len(char.monsters) else "no"

        variable_updates = {
            "party_healthy": party_healthy,
            "party_lost_hp": _lost_hp,
        }
        variables = [
            f"{key}:{value}"
            for key, value in variable_updates.items()
            if char.game_variables.get(key) != value
        ]

        if variables:
            for variable in variables:
                self.session.client.event_engine.execute_action(
                    "set_variable", [variable], True
                )
