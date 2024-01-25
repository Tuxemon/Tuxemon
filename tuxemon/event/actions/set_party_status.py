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
        character = get_npc(self.session, self.character)
        if character is None:
            logger.error(f"{self.character} not found")
            return
        if not character.monsters:
            logger.error(f"{character.name} has no monsters!")
            return

        # parameters
        level_lowest = MAX_LEVEL
        level_highest = 0
        level_average = 0

        # get values
        for npc_monster in character.monsters:
            if npc_monster.level < level_lowest:
                level_lowest = npc_monster.level
            if npc_monster.level > level_highest:
                level_highest = npc_monster.level
            level_average += npc_monster.level
        level_average = int(round(level_average / len(character.monsters)))

        # ship data in variables
        variable = character.game_variables
        variables: list[str] = []
        if variable.get("party_level_lowest", 0) != level_lowest:
            variables.append(f"party_level_lowest:{level_lowest}")
        if variable.get("party_level_highest", 0) != level_highest:
            variables.append(f"party_level_highest:{level_highest}")
        if variable.get("party_level_average", 0) != level_average:
            variables.append(f"party_level_average:{level_average}")
        client = self.session.client.event_engine
        if not variables:
            return
        for var in variables:
            client.execute_action("set_variable", [var], True)
