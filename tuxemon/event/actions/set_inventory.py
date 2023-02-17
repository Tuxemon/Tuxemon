# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import Union, final

from tuxemon.db import db
from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.item import item


@final
@dataclass
class SetInventoryAction(EventAction):
    """
    Overwrite the inventory of the npc or player.

    Script usage:
        .. code-block::

            set_inventory <npc_slug>,<inventory_slug>

    Script parameters:
        npc_slug: Either "player" or npc slug name (e.g. "npc_maple").
        inventory_slug: Slug of an inventory.

    """

    name = "set_inventory"
    npc_slug: str
    inventory_slug: Union[str, None] = None

    def start(self) -> None:
        npc = get_npc(self.session, self.npc_slug)
        assert npc
        if self.inventory_slug is None:
            npc.items = []
            return

        entry = db.lookup(
            self.inventory_slug,
            table="inventory",
        ).inventory

        for item_slug, quantity in entry.items():
            itm = item.Item()
            itm.load(item_slug)
            if quantity is None:
                itm.quantity = item.INFINITE_ITEMS
            else:
                itm.quantity = quantity
            npc.add_item(itm)
