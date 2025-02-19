# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import Optional, final

from tuxemon.event import get_monster_by_iid
from tuxemon.event.eventaction import EventAction

logger = logging.getLogger(__name__)


@final
@dataclass
class SetMonsterLevelAction(EventAction):
    """
    Change the level of a monster in the current player's party.

    Script usage:
        .. code-block::

            set_monster_level [variable][,levels_added]

    Script parameters:
        variable: Name of the variable where to store the monster id. If no
            variable is specified, all monsters level up.
        levels_added: Number of levels to add. Negative numbers are allowed.
            Default 1.

    """

    name = "set_monster_level"
    variable: Optional[str] = None
    levels_added: Optional[int] = None

    def start(self) -> None:
        player = self.session.player
        if not player.monsters:
            return
        if self.levels_added is None:
            self.levels_added = 1

        if self.variable is not None:
            if self.variable not in player.game_variables:
                logger.error(f"Game variable {self.variable} not found")
                return
            monster_id = uuid.UUID(player.game_variables[self.variable])
            monster = get_monster_by_iid(self.session, monster_id)
            if monster is None:
                logger.error("Monster not found")
                return
            new_level = monster.level + self.levels_added
            monster.set_level(new_level)
            monster.update_moves(self.levels_added)
        else:
            for monster in player.monsters:
                new_level = monster.level + self.levels_added
                monster.set_level(new_level)
                monster.update_moves(self.levels_added)
