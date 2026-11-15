# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import ClassVar

from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@dataclass
class PartyInfectedCondition(EventCondition):
    """
    Check to see how many monster are infected in the character's party.

    Script usage:
        .. code-block::

            is party_infected <character>,<plague_slug>,<value>

    Script parameters:
        character: Either "player" or npc slug name (e.g. "npc_maple").
        plague_slug: The slug of the plague to target.
        value: all, some or none.
    """

    name: ClassVar[str] = "party_infected"
    character: str
    plague_slug: str
    value: str

    def test(self, session: Session) -> bool:
        character = session.client.get_npc(self.character)
        if character is None:
            logger.error(f"{self.character} not found")
            return False

        plague = [
            mon
            for mon in character.monsters
            if mon.plague.has_plague(self.plague_slug)
            and mon.plague.is_infected_with(self.plague_slug)
        ]

        if self.value == "all":
            return len(plague) == len(character.monsters)
        elif self.value == "some":
            return len(character.monsters) > len(plague) > 0
        elif self.value == "none":
            return len(plague) == 0
        else:
            raise ValueError(f"{self.value} must be 'all', 'some' or 'none'")
