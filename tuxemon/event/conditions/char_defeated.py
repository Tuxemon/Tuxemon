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
class CharDefeatedCondition(EventCondition):
    """
    Check to see the character has at least one tuxemon, and all tuxemon in their
    party are defeated.

    Script usage:
        .. code-block::

            is char_defeated <character>

    Script parameters:
        character: Either "player" or character slug name (e.g. "npc_maple")
    """

    name = "char_defeated"

    def test(self, session: Session, condition: MapCondition) -> bool:
        character = get_npc(session, condition.parameters[0])
        if character is None:
            logger.error(f"{condition.parameters[0]} not found")
            return False

        if character.monsters:
            for mon in character.monsters:
                if mon.is_fainted and not mon.status.is_fainted:
                    mon.faint()
            return all(mon.status.is_fainted for mon in character.monsters)
        return False
