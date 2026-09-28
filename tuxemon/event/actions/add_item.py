# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.database.runtime import db
from tuxemon.event.eventaction import EventAction
from tuxemon.item.item import Item
from tuxemon.session import Session

logger = logging.getLogger(__name__)


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
    quantity: int | None = None
    npc_slug: str | None = None

    def start(self, session: Session) -> None:
        player = session.player
        self.npc_slug = self.npc_slug or "player"
        trainer = session.client.get_npc(self.npc_slug)
        if not trainer:
            raise ValueError(f"NPC '{self.npc_slug}' not found")

        if self.item_slug in db.database["item"]:
            item_id = self.item_slug
        elif player.game_variables.has(self.item_slug):
            item_id = player.game_variables.get(self.item_slug)
        else:
            raise ValueError(
                f"{self.item_slug} doesn't exist (item or variable)."
            )

        bag = trainer.bag
        existing = bag.find_item(item_id)

        qty = self.quantity if self.quantity is not None else 1

        if existing:
            if qty > 0:
                existing.increase_quantity(qty)
            elif qty < 0:
                bag.remove_item(existing, abs(qty))
            # qty == 0 → do nothing
            self.stop()
            return

        # No existing item
        if qty > 0:
            itm = Item.create(item_id)
            success = bag.add_item(itm, qty)
            if not success:
                logger.warning(
                    f"AddItemAction: Ignored invalid quantity {qty} for item '{item_id}' "
                    f"when adding to NPC '{trainer.slug}'."
                )
