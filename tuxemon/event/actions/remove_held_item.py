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
class RemoveHeldItemction(EventAction):
    """
    Removes a held item from a specific monster.

    Script usage:
        .. code-block::

            remove_held_item <variable>

    Script parameters:
        variable: Name of the variable where to store the monster id.

    """

    name = "remove_held_item"
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

        held = monster.held_item.get_item()
        if held is None:
            logger.error(f"{monster.name} doesn't held an item.")
            return

        item = monster.held_item.get_item()
        assert item
        logger.info(f"{item.name} has been removed from {monster.name}!")
        monster.held_item.clear_item()
