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
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session
from tuxemon.event import MapCondition
from typing import Optional


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
            return exists and player.game_variables[key] == value
