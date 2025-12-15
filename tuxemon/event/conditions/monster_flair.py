# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass

from tuxemon.db import SpatialCondition
from tuxemon.event import get_npc
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

    name = "monster_flair"

    def test(self, session: Session, condition: SpatialCondition) -> bool:
        if len(condition.parameters) < 3:
            logger.error(
                "monster_flair condition requires 3 parameters: character, category, name"
            )
            return False

        _character = condition.parameters[0]
        category = condition.parameters[1]
        name = condition.parameters[2]

        character = get_npc(session, _character)
        if character is None:
            logger.error(f"{_character} not found")
            return False

        for monster in character.party.monsters:
            if (
                monster.flairs.get(category)
                and monster.flairs[category].slug == name
            ):
                return True
        return False
