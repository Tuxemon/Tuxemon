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
class CharHealedCondition(EventCondition):
    """
    Check whether all monsters in the character's party are healed.

    Script usage:
        .. code-block::

            is char_healed <character>

    Script parameters:
        character: Either "player" or NPC slug name (e.g. "npc_maple")
    """

    name: ClassVar[str] = "char_healed"
    character: str

    def test(self, session: Session) -> bool:
        character = session.client.get_npc(self.character)
        if character is None:
            logger.error(f"{self.character} not found")
            return False

        if not character.monsters:
            return False

        return character.party.is_healed
