# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.states.world.worldstate import WorldState

logger = logging.getLogger(__name__)


@final
@dataclass
class RemoveTechAction(EventAction):
    """
    Remove a specific technique from a specific monster.

    Script usage:
        .. code-block::

            remove_tech <tech_id>

    Script parameters:
        tech_id: Name of the variable where to store the tech id.

    eg. "remove_tech name_variable"

    """

    name = "remove_tech"
    tech_id: str

    def start(self) -> None:
        world = self.session.client.get_state_by_name(WorldState)
        monsters = world.get_all_monsters()
        player = self.session.player
        if self.tech_id not in player.game_variables:
            logger.error(f"Game variable {self.tech_id} not found")
            return
        tech_id = uuid.UUID(player.game_variables[self.tech_id])

        for monster in monsters:
            technique = monster.find_tech_by_id(tech_id)
            if technique is None:
                logger.error(f"Technique isn't among {monster.name}'s moves")
                return
            monster.moves.remove(technique)
            logger.info(f"{technique.name} removed from {monster.name}")
