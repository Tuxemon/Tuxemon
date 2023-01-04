# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging

from tuxemon.event import MapCondition, get_npc
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session

logger = logging.getLogger(__name__)


class NPCFacingTileCondition(EventCondition):
    """
    Check to see if a character is facing a tile position.

    This is checked against all the tiles included in the condition object.

    Script usage:
        .. code-block::

            is npc_facing_tile <character>

    Script parameters:
        character: Either "player" or npc slug name (e.g. "npc_maple").

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

        for coordinates in tiles:
            # Next, we check the npc position and see if we're one tile away
            # from the tile.
            if coordinates[1] == npc.tile_pos[1]:
                # Check to see if the tile is to the left of the npc
                if coordinates[0] == npc.tile_pos[0] - 1:
                    logger.debug("Tile is to the left of the NPC")
                    tile_location = "left"
                # Check to see if the tile is to the right of the npc
                elif coordinates[0] == npc.tile_pos[0] + 1:
                    logger.debug("Tile is to the right of the NPC")
                    tile_location = "right"

            if coordinates[0] == npc.tile_pos[0]:
                # Check to see if the tile is above the npc
                if coordinates[1] == npc.tile_pos[1] - 1:
                    logger.debug("Tile is above the NPC")
                    tile_location = "up"
                elif coordinates[1] == npc.tile_pos[1] + 1:
                    logger.debug("Tile is below the NPC")
                    tile_location = "down"

            # Then we check to see the npc is facing the Tile
            if npc.facing == tile_location:
                return True

        return False
