#
# Tuxemon
# Copyright (c) 2014-2017 William Edwards <shadowapex@gmail.com>,
#                         Benjamin Bean <superman2k5@gmail.com>
#
# This file is part of Tuxemon
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

from __future__ import annotations

from typing import NamedTuple, Optional, final

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.item.economy import Economy
from tuxemon.states.choice import ChoiceState
from tuxemon.states.items import ShopBuyMenuState, ShopSellMenuState
from tuxemon.tools import assert_never, open_choice_dialog


class OpenShopActionParameters(NamedTuple):
    npc_slug: str
    menu: Optional[str]


@final
class OpenShopAction(EventAction[OpenShopActionParameters]):
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
    param_class = OpenShopActionParameters

    def start(self) -> None:
        npc = get_npc(self.session, self.parameters.npc_slug)

        assert npc
        if npc.economy:
            economy = npc.economy
        else:
            economy = Economy("default")

        def push_buy_menu():
            self.session.client.push_state(
                ShopBuyMenuState(
                    buyer=self.session.player,
                    seller=npc,
                    economy=economy,
                )
            )

        def push_sell_menu():
            self.session.client.push_state(
                ShopSellMenuState(
                    buyer=None,
                    seller=self.session.player,
                    economy=economy,
                )
            )

        menu = self.parameters.menu or "both"
        if menu == "both":

            def buy_menu() -> None:
                self.session.client.pop_state()
                push_buy_menu()

            def sell_menu() -> None:
                self.session.client.pop_state()
                push_sell_menu()

            var_menu = [
                ("Buy", "Buy", buy_menu),
                ("Sell", "Sell", sell_menu),
            ]

            self.session.client.push_state(
                ChoiceState(
                    menu=var_menu,
                    escape_key_exits=True,
                )
            )

        elif menu == "buy":
            push_buy_menu()
        elif menu == "sell":
            push_sell_menu()
        else:
            assert_never(menu)
