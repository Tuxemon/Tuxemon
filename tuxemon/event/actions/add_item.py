# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Union, final

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.item import item
from tuxemon.npc import NPC


@final
@dataclass
class AddItemAction(EventAction):
    """
    Add an item to the specified trainer's inventory.

    Script usage:
        .. code-block::

            add_item <item_slug>[,quantity][,trainer_slug]

    Script parameters:
        item_slug: Item name to look up in the item database.
        quantity: Quantity of the item to add or to reduce. By default it is 1.
        trainer_slug: Slug of the trainer that will receive the item. It
            defaults to the current player.

    """

    name = "add_item"
    item_slug: str
    quantity: Union[int, None] = None
    trainer_slug: Union[str, None] = None

    def start(self) -> None:
        trainer: Optional[NPC]

        if self.trainer_slug is None:
            trainer = self.session.player
        else:
            trainer = get_npc(self.session, self.trainer_slug)

        assert trainer, "No Trainer found with slug '{}'".format(
            self.trainer_slug or "player"
        )

        itm = item.Item()
        itm.load(self.item_slug)
        existing = trainer.find_item(self.item_slug)
        if existing:
            if self.quantity is None:
                existing.quantity += 1
            elif self.quantity < 0:
                diff = existing.quantity + self.quantity
                if diff <= 0:
                    trainer.remove_item(existing)
                else:
                    existing.quantity = diff
            elif self.quantity > 0:
                existing.quantity += self.quantity
            else:
                existing.quantity += 1
        else:
            if self.quantity is None:
                itm.quantity = 1
                trainer.add_item(itm)
            elif self.quantity > 0:
                itm.quantity = self.quantity
                trainer.add_item(itm)
            elif self.quantity < 0:
                return
            else:
                itm.quantity = 1
                trainer.add_item(itm)
