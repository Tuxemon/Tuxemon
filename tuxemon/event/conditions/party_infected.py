# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from operator import eq, ge, gt, le, lt, ne

from tuxemon.db import PlagueType
from tuxemon.event import MapCondition
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session


class PartyInfectedCondition(EventCondition):
    """
    Check to see how many monster are infected and stores the iids.

    Script usage:
        .. code-block::

            is party_infected <operator>,<value>

    Script parameters:
        operator: Numeric comparison operator. Accepted values are "less_than",
            "less_or_equal", "greater_than", "greater_or_equal", "equals"
            and "not_equals".
        value: The value to compare the party with.

    """

    name = "party_infected"

    def test(self, session: Session, condition: MapCondition) -> bool:
        """
        Check to see how many monsters are infected.

        Parameters:
            session: The session object
            condition: The map condition object.

        Returns:
            Whether the monsters are infected.

        """
        check = str(condition.parameters[0])
        number = int(condition.parameters[1])
        player = session.player
        infected = []
        for mon in player.monsters:
            if mon.plague == PlagueType.infected:
                infected.append(mon)
        party_size = len(infected)
        if check == "less_than":
            return bool(lt(party_size, number))
        elif check == "less_or_equal":
            return bool(le(party_size, number))
        elif check == "greater_than":
            return bool(gt(party_size, number))
        elif check == "greater_or_equal":
            return bool(ge(party_size, number))
        elif check == "equals":
            return bool(eq(party_size, number))
        elif check == "not_equals":
            return bool(ne(party_size, number))
        else:
            raise ValueError(f"{check} is incorrect.")
