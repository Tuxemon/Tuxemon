# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from typing import final

from tuxemon.database.runtime import db
from tuxemon.db import ItemModel
from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@final
@dataclass
class RandomItemAction(EventAction):
    """
    Picks a random item from a list and adds it to the trainer's inventory.

    Script usage:
        .. code-block::

            random_item <item_slugs>[,quantity][,trainer_slug]

    Script parameters:
        item_slugs:
            A colon-separated string of item slugs to choose from.
            Example: 'potion:super-potion:hyper-potion'.

            If omitted or empty, the action will load the full item cache
            and randomly select from *all available items* in the database.

        quantity:
            The number of the chosen item to add. Defaults to 1.

        trainer_slug:
            The slug of the trainer who will receive the item.
            Defaults to the current player.
    """

    name = "random_item"
    item_slug: str | None = None
    quantity: int | None = None
    trainer_slug: str | None = None

    def start(self, session: Session) -> None:

        if self.item_slug is None:
            ItemModel.load_cache(db)
            cache = ItemModel.get_cache()
            items = [item.slug for item in cache.values()]
        else:
            items = self.item_slug.split(":")

        if not items:
            logger.error("No valid items found for the given criteria.")
            self.stop()
            return

        chosen_item = random.choice(items)

        params: list[str | int] = [chosen_item]

        if self.trainer_slug is not None:
            params.append(self.quantity if self.quantity is not None else 1)
            params.append(self.trainer_slug)
        elif self.quantity is not None:
            params.append(self.quantity)

        session.client.event_engine.execute_action("add_item", params, True)
