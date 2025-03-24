# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import final

from tuxemon.event import get_monster_by_iid
from tuxemon.event.eventaction import EventAction
from tuxemon.item.item import Item

logger = logging.getLogger(__name__)


@final
@dataclass
class AddHeldItemction(EventAction):
    """
    Adds a held item to a specific monster.

    Script usage:
        .. code-block::

            add_held_item <variable>,<item>

    Script parameters:
        variable: Name of the variable where to store the monster id.
        item: Slug of the item (e.g. "potion").

    """

    name = "add_held_item"
    variable: str
    item: str

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
        if held is not None:
            logger.error(f"{monster.name} held already {held.name}")
            return

        item = Item()
        item.load(self.item)
        if item.behaviors.holdable == False:
            logger.error(f"{item.name} isn't holdable")
            return
        else:
            logger.info(f"{item.name} has been added to {monster.name}!")
            monster.held_item.set_item(item)
