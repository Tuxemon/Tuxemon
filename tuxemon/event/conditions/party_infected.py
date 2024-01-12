# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging

from tuxemon.db import PlagueType
from tuxemon.event import MapCondition, get_npc
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session

logger = logging.getLogger(__name__)


class PartyInfectedCondition(EventCondition):
    """
    Check to see how many monster are infected in the character's party.

    Script usage:
        .. code-block::

            is party_infected <character>,<value>

    Script parameters:
        character: Either "player" or npc slug name (e.g. "npc_maple").
        value: all, some or none.

    """

    name = "party_infected"

    def test(self, session: Session, condition: MapCondition) -> bool:
        _character, _value = condition.parameters[:2]
        _plague = PlagueType.infected
        character = get_npc(session, _character)
        if character is None:
            logger.error(f"{_character} not found")
            return False

        plague = [mon for mon in character.monsters if mon.plague == _plague]

        if _value == "all":
            return len(plague) == len(character.monsters)
        elif _value == "some":
            return len(character.monsters) > len(plague) > 0
        elif _value == "none":
            return len(plague) == 0
        else:
            raise ValueError(f"{_value} must be all, some or none")
