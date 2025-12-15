# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass

from tuxemon.db import SpatialCondition
from tuxemon.event import get_npc
from tuxemon.event.eventcondition import EventCondition
from tuxemon.prepare import SURFACE_KEYS
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@dataclass
class CharInCondition(EventCondition):
    """
    Check to see if the character is on a specific set of tiles.

    Script usage:
        .. code-block::

            is char_in <character>,<value>

    Script parameters:
        character: Either "player" or character slug name (e.g. "npc_maple")
        value: value (eg surfable) inside the tileset.
    """

    name = "char_in"

    def test(self, session: Session, condition: SpatialCondition) -> bool:
        client = session.client
        character = get_npc(session, condition.parameters[0])
        if character is None:
            logger.error(f"{condition.parameters[0]} not found")
            return False
        prop = condition.parameters[1]

        tiles = []
        if prop in SURFACE_KEYS:
            tiles = client.collision_manager.get_all_tile_properties(
                client.map_manager.surface_map, prop
            )
        else:
            tiles = client.collision_manager.check_collision_zones(
                client.map_manager.collision_map, prop
            )
        if tiles:
            return character.tile_pos in tiles
        return False
