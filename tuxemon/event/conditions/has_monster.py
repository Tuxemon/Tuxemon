# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass

from tuxemon.event import MapCondition, get_npc
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

    name = "has_monster"

    def test(self, session: Session, condition: MapCondition) -> bool:
        _character, _monster = condition.parameters[:2]
        character = get_npc(session, _character)
        if character is None:
            logger.error(f"{_character} not found")
            return False
        if character.find_monster(_monster):
            return True
        return False
