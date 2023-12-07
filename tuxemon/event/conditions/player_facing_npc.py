# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging

from tuxemon.event import MapCondition, get_npc
from tuxemon.event.eventcondition import EventCondition
from tuxemon.map import get_coords, get_direction
from tuxemon.session import Session

logger = logging.getLogger(__name__)


class PlayerFacingNPCCondition(EventCondition):
    """
    Check to see the player is next to and facing a particular NPC.

    Script usage:
        .. code-block::

            is player_facing_npc <character>

    Script parameters:
        character: Npc slug name (e.g. "npc_maple").

    """

    name = "player_facing_npc"

    def test(self, session: Session, condition: MapCondition) -> bool:
        """
        Check to see the player is next to and facing a particular NPC.

        Parameters:
            session: The session object
            condition: The map condition object.

        Returns:
            Whether the player is facing the chosen character.

        """
        client = session.client
        npc_location = None

        player = get_npc(session, "player")
        npc = get_npc(session, condition.parameters[0])
        if not npc or not player:
            return False

        # get all the coordinates around the npc
        npc_tiles = get_coords(npc.tile_pos, client.map_size)
        npc_location = get_direction(player.tile_pos, npc.tile_pos)

        if player.tile_pos in npc_tiles:
            logger.debug(
                f"{player.name} is facing {npc_location} at {npc.slug}"
            )
            return player.facing == npc_location

        return False
