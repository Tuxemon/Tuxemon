# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging

from tuxemon.event import MapCondition
from tuxemon.event.eventcondition import EventCondition
from tuxemon.map import get_coords, get_direction
from tuxemon.session import Session
from tuxemon.states.world.worldstate import WorldState

logger = logging.getLogger(__name__)


class PlayerFacingTileCondition(EventCondition):
    """
    Check to see if an NPC is facing a tile position.

    Script usage:
        .. code-block::

            is player_facing_tile [value]

    Script parameters:
        value: value (eg surfable) inside the tileset.

    """

    name = "player_facing_tile"

    def test(self, session: Session, condition: MapCondition) -> bool:
        """
        Check to see the player is facing a tile position.

        Parameters:
            session: The session object
            condition: The map condition object.

        Returns:
            Whether the player faces one of the condition tiles.

        """

        tiles = [
            (condition.x + w, condition.y + h)
            for w in range(0, condition.width)
            for h in range(0, condition.height)
        ]
        tile_location = None
        player = session.player
        client = session.client
        # get all the coordinates around the player
        player_tiles = get_coords(player.tile_pos, client.map_size)

        # check if the NPC is facing a specific set of tiles
        world = session.client.get_state_by_name(WorldState)
        if condition.parameters:
            prop = condition.parameters[0]
            if prop == "surfable":
                surf = list(world.surfable_map)
                tiles = list(set(player_tiles).intersection(surf))

        # return common coordinates
        tiles = list(set(tiles).intersection(player_tiles))

        for coords in tiles:
            # Look through the remaining tiles and get directions
            tile_location = get_direction(player.tile_pos, coords)
            # Then we check to see if we're facing the Tile
            if player.facing == tile_location:
                logger.debug(f"Player is facing {tile_location}")
                return True

        return False
