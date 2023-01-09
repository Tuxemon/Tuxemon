# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import final

from tuxemon.db import db
from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.item.item import decode_inventory


@final
@dataclass
class UpdateInventoryAction(EventAction):
    """
    Update the inventory of the npc or player.

    Overwrites the quantity of an item if it's already present,
    but leaves other items alone.

    Script usage:
        .. code-block::

            update_inventory <npc_slug>,<inventory_slug>

    Script parameters:
        npc_slug: Either "player" or npc slug name (e.g. "npc_maple").
        inventory_slug: Slug of an inventory.

    """

    name = "update_inventory"
    npc_slug: str
    inventory_slug: str

    def start(self) -> None:
        npc = get_npc(self.session, self.npc_slug)
        assert npc
        if self.inventory_slug is None:
            return

        npc.inventory.update(
            decode_inventory(
                self.session,
                npc,
                db.lookup(
                    self.inventory_slug,
                    table="inventory",
                ).inventory,
            )
        )
