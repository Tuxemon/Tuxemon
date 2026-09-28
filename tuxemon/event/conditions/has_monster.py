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
class HasMonsterCondition(EventCondition):
    """
    Check to see if a character has a monster in its party.

    Script usage:
        .. code-block::

            is has_monster <character>,<monster>

    Script parameters:
        character: Either "player" or npc slug name (e.g. "npc_maple").
        monster: Monster slug name (e.g. "rockitten").
    """

    name: ClassVar[str] = "has_monster"
    character: str
    monster: str

    def test(self, session: Session) -> bool:
        character = session.client.get_npc(self.character)
        if character is None:
            logger.error(f"{self.character} not found")
            return False
        if character.party.find_monster(self.monster):
            return True
        return False
