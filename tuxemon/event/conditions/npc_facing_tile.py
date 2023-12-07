# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging

from tuxemon.event import MapCondition, get_npc
from tuxemon.event.eventcondition import EventCondition
from tuxemon.map import get_coords, get_direction
from tuxemon.session import Session
from tuxemon.states.world.worldstate import WorldState

logger = logging.getLogger(__name__)


class NPCFacingTileCondition(EventCondition):
    """
    Check to see if a character is facing a tile position.

    This is checked against all the tiles included in the condition object.

    Script usage:
        .. code-block::

            is npc_facing_tile <character>[,value]

    Script parameters:
        character: Either "player" or npc slug name (e.g. "npc_maple").
        value: value (eg surfable) inside the tileset.

    """

    name = "npc_facing_tile"

    def test(self, session: Session, condition: MapCondition) -> bool:
        """
        Check to see if a character is facing a tile position.

        Parameters:
            session: The session object
            condition: The map condition object.

        Returns:
            Whether the chosen character faces one of the condition tiles.

        """
        # Get the npc object from the game.
        npc = get_npc(session, condition.parameters[0])
        if not npc:
            return False

        tiles = [
            (condition.x + w, condition.y + h)
            for w in range(0, condition.width)
            for h in range(0, condition.height)
        ]
        tile_location = None
        # get all the coordinates around the npc
        client = session.client
        npc_tiles = get_coords(npc.tile_pos, client.map_size)

        # check if the NPC is facing a specific set of tiles
        world = session.client.get_state_by_name(WorldState)
        if len(condition.parameters) > 1:
            value = condition.parameters[1]
            if value == "surfable":
                label = list(world.surfable_map)
            else:
                label = world.check_collision_zones(world.collision_map, value)
            tiles = list(set(npc_tiles).intersection(label))

        # return common coordinates
        tiles = list(set(tiles).intersection(npc_tiles))

        for coords in tiles:
            # Look through the remaining tiles and get directions
            tile_location = get_direction(npc.tile_pos, coords)
            # Then we check to see the npc is facing the Tile
            if npc.facing == tile_location:
                logger.debug(f"{npc.slug} is facing {tile_location}")
                return True

        return False
