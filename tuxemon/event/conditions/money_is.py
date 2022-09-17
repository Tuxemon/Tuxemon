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


class MoneyIsCondition(EventCondition):
    """
    Check to see if the player has seen or caught a monster.

    Script usage:
        .. code-block::

            is money_is <slug>,<operator>,<value>

    Script parameters:
        slug: Slug name (e.g. player or NPC, etc.).
        operator: One of "==", "!=", ">", ">=", "<" or "<=".
        amount: amoung of money

    """

    name = "money_is"

    def test(self, session: Session, condition: MapCondition) -> bool:
        """
        Check to see if the player has seen or caught a monster.

        Parameters:
            session: The session object
            condition: The map condition object.

        Returns:
            Whether the player has seen or caught a monster.

        """
        player = session.player

        # Read the parameters
        wallet = condition.parameters[0]
        operator = condition.parameters[1]
        amount = condition.parameters[2]

        # Check if the condition is true
        if wallet in player.money:
            if operator == "==":
                return player.money[wallet] == int(amount)
            elif operator == "!=":
                return player.money[wallet] != int(amount)
            elif operator == ">":
                return player.money[wallet] > int(amount)
            elif operator == ">=":
                return player.money[wallet] >= int(amount)
            elif operator == "<":
                return player.money[wallet] < int(amount)
            elif operator == "<=":
                return player.money[wallet] <= int(amount)
            else:
                raise ValueError(f"invalid operation type {operator}")
        else:
            return False
