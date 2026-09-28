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

    name: ClassVar[str] = "char_defeated"
    character: str

    def test(self, session: Session) -> bool:
        character = session.client.get_npc(self.character)
        if character is None:
            logger.error(f"{self.character} not found")
            return False

        if character.monsters:
            for mon in character.monsters:
                if mon.is_fainted and not mon.status.is_fainted:
                    mon.current_hp = 0
                    mon.status.apply_faint(session, mon)
            return all(mon.status.is_fainted for mon in character.monsters)
        return False
