# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Union, final

from tuxemon.db import db
from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.item.item import Item
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
        player = self.session.player
        trainer: Optional[NPC]
        if self.trainer_slug is None:
            trainer = player
        else:
            trainer = get_npc(self.session, self.trainer_slug)

        assert trainer, "No Trainer found with slug '{}'".format(
            self.trainer_slug or "player"
        )

        # check item existence
        _item: str = ""
        verify = list(db.database["item"])
        if self.item_slug not in verify:
            if self.item_slug in player.game_variables:
                _item = player.game_variables[self.item_slug]
            else:
                raise ValueError(
                    f"{self.item_slug} doesn't exist (item or variable)."
                )
        else:
            _item = self.item_slug

        itm = Item()
        itm.load(_item)
        existing = trainer.find_item(_item)
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
