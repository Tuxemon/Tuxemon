# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import Optional, final

from tuxemon.db import PlagueType
from tuxemon.event import get_monster_by_iid
from tuxemon.event.eventaction import EventAction

logger = logging.getLogger(__name__)


@final
@dataclass
class SetMonsterPlagueAction(EventAction):
    """
    Set a monster's plague to the given condition.

    Script usage:
        .. code-block::

            set_monster_plague <variable>,<plague_slug>,<condition>

    Script parameters:
        variable: Name of the variable where to store the monster id.
        plague_slug: The slug of the plague to target.
        condition: Infected, inoculated, or None (removes the plague from the
            character, indicating a healthy state).

    """

    name = "set_monster_plague"
    variable: str
    plague_slug: str
    condition: Optional[str] = None

    def start(self) -> None:
        player = self.session.player
        if self.variable not in player.game_variables:
            logger.error(f"Game variable {self.variable} not found")
            return

        monster_id = uuid.UUID(player.game_variables[self.variable])
        monster = get_monster_by_iid(self.session, monster_id)
        if monster is None:
            logger.error("Monster not found")
            return

        if self.condition is None:
            monster.plague = {}
        elif self.condition == "infected":
            monster.plague[self.plague_slug] = PlagueType.infected
        elif self.condition == "inoculated":
            monster.plague[self.plague_slug] = PlagueType.inoculated
        else:
            raise ValueError(
                f"{self.condition} must be 'infected' or 'inoculated'."
            )
