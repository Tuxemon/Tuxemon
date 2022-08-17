#
# Tuxemon
# Copyright (c) 2014-2017 William Edwards <shadowapex@gmail.com>,
#                         Benjamin Bean <superman2k5@gmail.com>
#
# This file is part of Tuxemon
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
from __future__ import annotations

import logging

from tuxemon.event import MapCondition
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session

logger = logging.getLogger(__name__)


class BattleIsCondition(EventCondition):
    """
    Check an operation over a battle.

    Script usage:
        .. code-block::

            is battle_is <character>,<result>,<operation>,<value>

    Script parameters:
        character: Npc slug name (e.g. "npc_maple").
        result: One of "won", "lost" or "draw"
        operation: One of "==", "!=", ">", ">=", "<" or "<=".
        value: A number.

    """

    name = "battle_is"

    def test(self, session: Session, condition: MapCondition) -> bool:
        """
        Check an operation over a variable.

        Parameters:
            session: The session object
            condition: The map condition object.

        Returns:
            Result of the operation over the variable.

        """
        player = session.player

        # Read the parameters
        npc = condition.parameters[0]
        result = condition.parameters[1]
        operation = condition.parameters[2]
        value = condition.parameters[3]

        # Union
        battle_mix = str(npc) + " - " + result

        # Count
        count = 0
        for val in player.battle_history.values():
            if val == battle_mix:
                count += 1

        # Check if the condition is true
        if operation == "==":
            return int(count) == int(value)
        elif operation == "!=":
            return int(count) != int(value)
        elif operation == ">":
            return int(count) > int(value)
        elif operation == ">=":
            return int(count) >= int(value)
        elif operation == "<":
            return int(count) < int(value)
        elif operation == "<=":
            return int(count) <= int(value)
        else:
            logger.error(f"invalid operation type {operation}")
            raise ValueError
