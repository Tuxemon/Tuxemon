# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import final

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.item.economy import Economy
from tuxemon.item.item import Item


@final
@dataclass
class SetEconomyAction(EventAction):
    """
    Set the economy (prices of items) of the npc or player.

    Script usage:
        .. code-block::

            set_economy <npc_slug>,<economy_slug>

    Script parameters:
        npc_slug: Either "player" or npc slug name (e.g. "npc_maple").
        economy_slug: Slug of an economy.

    """

    name = "set_economy"
    npc_slug: str
    economy_slug: str

    def start(self) -> None:
        player = self.session.player
        npc = get_npc(self.session, self.npc_slug)
        assert npc

        def variable(var: str) -> bool:
            variables = var.split(":")
            return variables[1] == player.game_variables.get(variables[0])

        npc.economy = Economy(self.economy_slug)

        for itm in npc.economy.items:
            label = f"{self.economy_slug}:{itm.item_name}"
            # saving quantities inside variables
            if label not in player.game_variables:
                player.game_variables[label] = itm.inventory

            itm_in_shop = Item()
            if itm.variable:
                if variable(itm.variable):
                    itm_in_shop.load(itm.item_name)
                    itm_in_shop.quantity = int(player.game_variables[label])
                    npc.add_item(itm_in_shop)
            else:
                itm_in_shop.load(itm.item_name)
                itm_in_shop.quantity = int(player.game_variables[label])
                npc.add_item(itm_in_shop)
