# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import Optional, final

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
        tech_id: Id of the technique (name of the variable).

    eg. "remove_tech name_variable"

    """

    name = "remove_tech"
    tech_id: str
    npc_slug: Optional[str] = None

    def start(self) -> None:
        world = self.session.client.get_state_by_name(WorldState)
        monsters = world.get_all_monsters()
        player = self.session.player

        # look for the technique
        tech_id = uuid.UUID(
            player.game_variables[self.tech_id],
        )

        for monster in monsters:
            technique = monster.find_tech_by_id(tech_id)
            if technique:
                monster.moves.remove(technique)
                logger.info(f"{technique.name} removed from {monster.name}")
