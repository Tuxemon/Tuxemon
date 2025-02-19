# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import final

from tuxemon.event import get_monster_by_iid
from tuxemon.event.eventaction import EventAction

logger = logging.getLogger(__name__)


@final
@dataclass
class RemoveMonsterAction(EventAction):
    """
    Remove a monster from the party if the monster is there.

    Monster is determined by instance_id, which must be passed in a game
    variable.

    Script usage:
        .. code-block::

            remove_monster <variable>

    Script parameters:
        variable: Name of the variable where to store the monster id.

    """

    name = "remove_monster"
    variable: str

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
        character = monster.owner
        if character is None:
            logger.error(f"{monster.name}'s owner not found!")
            return
        logger.info(f"{monster.name} removed from {character.name} party!")
        character.remove_monster(monster)
