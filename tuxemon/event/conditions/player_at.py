# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from tuxemon.event import MapCondition
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session


class PlayerAtCondition(EventCondition):
    """
    Check to see if the player is at the condition position on the map.

    Script usage:
        .. code-block::

            is player_at

    """

    name = "player_at"

    def test(self, session: Session, condition: MapCondition) -> bool:
        """
        Check to see if the player is at the condition position on the map.

        Parameters:
            session: The session object
            condition: The map condition object.

        Returns:
            Whether the player is in the condition position.

        """
        player = session.player

        # Get the condition's rectangle area. If we're on a tile in that area,
        # then this condition should return True.
        area_x = range(condition.x, condition.x + condition.width)
        area_y = range(condition.y, condition.y + condition.height)

        # If the player is at the coordinates and the operator is set to true
        # then return true
        return (
            round(player.tile_pos[0]) in area_x
            and round(player.tile_pos[1]) in area_y
        )
