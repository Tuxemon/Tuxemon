# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Optional, final

from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session


@final
@dataclass
class RandomItemAction(EventAction):
    """
    Pick a random item from a list and add it to the trainer's inventory.

    Script usage:
        .. code-block::

            random_item <item_slug>[,quantity][,trainer_slug]

    Script parameters:
        item_slug: Item name to look up in the item database (multiple items
        separate by ":").
        quantity: Quantity of the item to add or to reduce. By default it is 1.
        trainer_slug: Slug of the trainer that will receive the item. It
            defaults to the current player.

    """

    name = "random_item"
    item_slug: str
    quantity: Optional[int] = None
    trainer_slug: Optional[str] = None

    def start(self, session: Session) -> None:
        # check if multiple items
        item: str = ""
        items: list[str] = []
        if self.item_slug.find(":"):
            items = self.item_slug.split(":")
            item = random.choice(items)
        else:
            item = self.item_slug

        session.client.event_engine.execute_action(
            "add_item", [item, self.quantity, self.trainer_slug], True
        )
