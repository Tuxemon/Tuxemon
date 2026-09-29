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
class MonsterFlairCondition(EventCondition):
    """
    Check if any monster in the character's party has a flair matching the
    given category and name.

    Script usage:
        .. code-block::

            is monster_flair <character>,<category>,<name>

    Script parameters:
        character: Either "player" or an NPC slug name (e.g. "npc_maple").
        category: Category of the flair to check.
        name: Name of the flair to match.

    Behavior:
        - Returns True if any monster in the character's party has a flair
            in the given category with the specified name.
        - Returns False if no match is found or the character is invalid.
    """

    name: ClassVar[str] = "monster_flair"
    character: str
    category: str
    flair_name: str

    def test(self, session: Session) -> bool:
        character = session.client.get_npc(self.character)
        if character is None:
            logger.error(f"{self.character} not found")
            return False

        for monster in character.party.monsters:
            if (
                monster.flairs.get(self.category)
                and monster.flairs[self.category].slug == self.flair_name
            ):
                return True
        return False
