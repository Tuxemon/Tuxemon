# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final
from uuid import UUID

from tuxemon.event import get_monster_by_iid
from tuxemon.event.eventaction import EventAction
from tuxemon.item.item import Item
from tuxemon.session import Session

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

    def start(self, session: Session) -> None:
        player = session.player
        if not player.game_variables.has(self.variable):
            logger.error(f"Game variable {self.variable} not found")
            return

        monster_id = UUID(player.game_variables.get(self.variable))
        monster = get_monster_by_iid(session, monster_id)
        if monster is None:
            logger.error("Monster not found")
            return

        held = monster.held_item
        if held is not None:
            logger.error(f"{monster.name} held already {held.name}")
            return

        item = Item.create(self.item)
        output = monster.item_handler.set_item(item)
        if not output:
            return
