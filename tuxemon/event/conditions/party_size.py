# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging

from tuxemon.event import MapCondition
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session

logger = logging.getLogger(__name__)


class PartySizeCondition(EventCondition):
    """
    Check the party size.

    Script usage:
        .. code-block::

            is party_size <operator>,<value>

    Script parameters:
        operator: One of "equals", "less_than" or "greater_than".
        value: The value to compare the party size with.

    """

    name = "party_size"

    def test(self, session: Session, condition: MapCondition) -> bool:
        """
        Check the party size.

        Parameters:
            session: The session object
            condition: The map condition object.

        Returns:
            Result of the comparison between the party size and the chosen
            value.

        """
        check = str(condition.parameters[0])
        number = int(condition.parameters[1])
        party_size = len(session.player.monsters)

        # Check to see if the player's party size equals this number.
        if check == "equals":
            logger.debug("Equal check")
            return party_size == number

        # Check to see if the player's party size is LESS than this number.
        elif check == "less_than":
            return party_size < number

        # Check to see if the player's part size is GREATER than this number.
        elif check == "greater_than":
            return party_size > number

        else:
            raise Exception("Party size check parameters are incorrect.")
