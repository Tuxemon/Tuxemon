# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from typing import Optional

from tuxemon.event import MapCondition
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session

logger = logging.getLogger(__name__)


class VariableSetCondition(EventCondition):
    """
    Check to see if a player game variable exists and has a particular value.

    If the variable does not exist it will return ``False``.

    Script usage:
        .. code-block::

            is variable_set <variable>[:value]

    Script parameters:
        variable: The variable to check.
        value: Optional value to check for.

    """

    name = "variable_set"

    def test(self, session: Session, condition: MapCondition) -> bool:
        """
        Check to see if a player game variable has a particular value.

        Parameters:
            session: The session object
            condition: The map condition object.

        Returns:
            Whether the variable exists and has that value.

        """
        player = session.player

        parts = condition.parameters[0].split(":")
        key = parts[0]
        if len(parts) > 1:
            value: Optional[str] = parts[1]
        else:
            value = None

        exists = key in player.game_variables

        if value is None:
            return exists
        else:
            logger.info(f"Game variable {key} has value: {value}")
            return exists and player.game_variables[key] == value
