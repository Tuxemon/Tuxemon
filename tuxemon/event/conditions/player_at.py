# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from tuxemon.event import MapCondition, collide
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
        return collide(condition, player.tile_pos)
