# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import final

from tuxemon.event import get_monster_by_iid
from tuxemon.event.eventaction import EventAction
from tuxemon.monster import Flair

logger = logging.getLogger(__name__)


@final
@dataclass
class SetMonsterFlairAction(EventAction):
    """
    Set a monster's flair to the given value.

    Script usage:
        .. code-block::

            set_monster_flair <variable>,<category>,<flair>

    Script parameters:
        variable: Name of the variable where to store the monster id. If no
            variable is specified, all monsters are changed.
        category: Category of the monster flair.
        flair: Name of the monster flair.

    """

    name = "set_monster_flair"
    variable: str
    category: str
    flair: str

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
        if self.category in monster.flairs:
            monster.flairs[self.category] = Flair(
                self.category,
                self.flair,
            )
