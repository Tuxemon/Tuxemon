# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from functools import partial
from typing import Optional, final

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.item.economy import Economy
from tuxemon.npc import NPC
from tuxemon.states.choice import ChoiceState
from tuxemon.states.items import ShopBuyMenuState, ShopSellMenuState


@final
@dataclass
class OpenShopAction(EventAction):
    """
    Open the shop menu for a NPC.

    Script usage:
        .. code-block::

            open_shop <npc_slug>,[menu]

    Script parameters:
        npc_slug: Either "player" or npc slug name (e.g. "npc_maple").
        menu: Either "buy", "sell" or "both". Default is "both".

    """

    name = "open_shop"
    npc_slug: str
    menu: Optional[str] = None

    def start(self) -> None:
        npc = get_npc(self.session, self.npc_slug)

        assert npc
        if npc.economy:
            economy = npc.economy
        else:
            economy = Economy("default")

        def push_buy_menu(npc: NPC) -> None:
            self.session.client.push_state(
                ShopBuyMenuState(
                    buyer=self.session.player,
                    seller=npc,
                    economy=economy,
                )
            )

        def push_sell_menu(npc: NPC) -> None:
            self.session.client.push_state(
                ShopSellMenuState(
                    buyer=npc,
                    seller=self.session.player,
                    economy=economy,
                )
            )

        menu = self.menu or "both"
        if menu == "both":

            def buy_menu(npc: NPC) -> None:
                self.session.client.pop_state()
                push_buy_menu(npc)

            def sell_menu(npc: NPC) -> None:
                self.session.client.pop_state()
                push_sell_menu(npc)

            var_menu = [
                ("Buy", "Buy", partial(buy_menu, npc)),
                ("Sell", "Sell", partial(sell_menu, npc)),
            ]

            self.session.client.push_state(
                ChoiceState(
                    menu=var_menu,
                    escape_key_exits=True,
                )
            )

        elif menu == "buy":
            push_buy_menu(npc)
        elif menu == "sell":
            push_sell_menu(npc)
        else:
            raise Exception(
                f"The parameter {self.menu} can be only 'both', 'buy' or 'sell'."
            )
