# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.item.item import Item
from tuxemon.session import Session
from tuxemon.tools import get_valid_uuid

logger = logging.getLogger(__name__)


@final
@dataclass
class AddHeldItemAction(EventAction):
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

        monster_id = get_valid_uuid(player.game_variables, self.variable)
        if monster_id is None:
            logger.info(
                f"No valid monster selected for variable '{self.variable}'"
            )
            self.stop()
            return  # Exit early if no valid UUID

        monster = session.client.get_monster_by_iid(monster_id)
        if monster is None:
            logger.error("Monster not found")
            self.stop()
            return

        held = monster.held_item
        if held is not None:
            logger.error(f"{monster.name} held already {held.name}")
            self.stop()
            return

        item = Item.create(self.item)
        output = monster.equip_item(item)
        if not output:
            self.stop()
            return
