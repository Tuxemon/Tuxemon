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
class CharGenderCondition(EventCondition):
    """
    Check whether a character's gender matches the expected value.

    Script usage:
        .. code-block::

            is char_gender <character> <gender>

    Script parameters:
        character: Either "player" or an NPC slug (e.g. "npc_maple")
        gender: Expected gender string to compare against the character's gender
    """

    name: ClassVar[str] = "char_gender"
    character: str
    gender: str

    def test(self, session: Session) -> bool:
        char_slug = self.character
        expected_gender = self.gender.strip().lower()

        character = session.client.get_npc(char_slug)
        if character is None:
            logger.error(f"{char_slug} not found")
            return False

        # Script says: char_gender player,none
        if expected_gender in ("none", "null", ""):
            return character.gender is None

        # Character has no gender set
        if character.gender is None:
            return False

        # Normal comparison
        return character.gender.lower() == expected_gender
