# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging

from tuxemon.db import PlagueType
from tuxemon.event import MapCondition
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session

logger = logging.getLogger(__name__)


class PartyInfectedCondition(EventCondition):
    """
    Check to see how many monster are infected and stores the iids.

    Script usage:
        .. code-block::

            is party_infected <value>

    Script parameters:
        value: all, some or none.

    """

    name = "party_infected"

    def test(self, session: Session, condition: MapCondition) -> bool:
        value = str(condition.parameters[0])
        player = session.player
        infected = []
        for mon in player.monsters:
            if mon.plague == PlagueType.infected:
                infected.append(mon)
        if value == "all":
            if len(infected) == len(player.monsters):
                return True
            else:
                return False
        elif value == "some":
            if len(infected) > 0 and len(infected) < len(player.monsters):
                return True
            else:
                return False
        elif value == "none":
            if len(infected) == 0:
                return True
            else:
                return False
        else:
            logger.error(f"{value} must be all, some or none")
            raise ValueError()
