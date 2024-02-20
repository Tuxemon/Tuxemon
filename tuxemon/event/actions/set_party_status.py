# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.prepare import MAX_LEVEL

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

        # parameters
        level_lowest = MAX_LEVEL
        level_highest = 0
        level_average = 0
        _healthy = 0
        _lost_hp = 0

        # get values
        for monster in char.monsters:
            if monster.level < level_lowest:
                level_lowest = monster.level
            if monster.level > level_highest:
                level_highest = monster.level
            if monster.current_hp == monster.hp:
                _healthy += 1
            _lost_hp += monster.hp - monster.current_hp
            level_average += monster.level

        level_average = int(round(level_average / len(char.monsters)))
        party_healthy = "yes" if _healthy == len(char.monsters) else "no"

        # ship data in variables
        variable = char.game_variables
        variables: list[str] = []
        if variable.get("party_level_lowest", 0) != level_lowest:
            variables.append(f"party_level_lowest:{level_lowest}")
        if variable.get("party_level_highest", 0) != level_highest:
            variables.append(f"party_level_highest:{level_highest}")
        if variable.get("party_level_average", 0) != level_average:
            variables.append(f"party_level_average:{level_average}")
        if variable.get("party_healthy", "no") != party_healthy:
            variables.append(f"party_healthy:{party_healthy}")
        if variable.get("party_lost_hp", 0) != _lost_hp:
            variables.append(f"party_lost_hp:{_lost_hp}")

        if variables:
            client = self.session.client.event_engine
            for var in variables:
                client.execute_action("set_variable", [var], True)
