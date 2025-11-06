# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, final

from tuxemon.db import db
from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.item.item import Item
from tuxemon.session import Session


@final
@dataclass
class AddItemAction(EventAction):
    """
    Add an item to the specified trainer's inventory.

    Script usage:
        .. code-block::

            add_item <item_slug>[,quantity][,npc_slug]

    Script parameters:
        item_slug: Item name to look up in the item database.
        quantity: Quantity of the item to add or to reduce. By default it is 1.
        npc_slug: Slug of the trainer that will receive the item. It
            defaults to the current player.
    """

    name = "add_item"
    item_slug: str
    quantity: Optional[int] = None
    npc_slug: Optional[str] = None

    def start(self, session: Session) -> None:
        player = session.player
        self.npc_slug = self.npc_slug or "player"
        trainer = get_npc(session, self.npc_slug)
        if not trainer:
            raise ValueError(f"NPC '{self.npc_slug}' not found")

        # check item existence
        item_id: str = ""
        if self.item_slug not in db.database["item"]:
            if player.game_variables.has(self.item_slug):
                item_id = player.game_variables.get(self.item_slug)
            else:
                raise ValueError(
                    f"{self.item_slug} doesn't exist (item or variable)."
                )
        else:
            item_id = self.item_slug

        existing = trainer.bag.find_item(item_id)

        if existing:
            if self.quantity is None or self.quantity == 0:
                existing.increase_quantity()
            elif self.quantity > 0:
                existing.increase_quantity(self.quantity)
            elif self.quantity < 0:
                trainer.bag.remove_item(existing, abs(self.quantity))
        elif self.quantity is None or self.quantity > 0:
            itm = Item.create(item_id)
            trainer.bag.add_item(itm, self.quantity or 1)
