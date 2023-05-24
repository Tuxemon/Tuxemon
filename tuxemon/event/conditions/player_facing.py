# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging

from tuxemon.event import MapCondition
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session

logger = logging.getLogger(__name__)


class PlayerFacingCondition(EventCondition):
    """
    Check to see where an NPC is facing.

    Script usage:
        .. code-block::

            is player_facing <direction>

    Script parameters:
        direction: One of "up", "down", "left" or "right".

    """

    name = "player_facing"

    def test(self, session: Session, condition: MapCondition) -> bool:
        """
        Check to see where the player is facing

        Parameters:
            session: The session object
            condition: The map condition object.

        Returns:
            Whether the player faces the chosen direction.

        """
        player = session.player
        facing = condition.parameters[0]
        directions = ["up", "down", "left", "right"]
        if facing not in directions:
            logger.error(f"{facing} must be 'up', 'down', 'left' or 'right'")
            raise ValueError()
        else:
            return player.facing == facing
