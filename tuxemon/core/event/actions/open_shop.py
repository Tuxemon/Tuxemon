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

from tuxemon.core.event import get_npc
from tuxemon.core.event.eventaction import EventAction


class OpenShopAction(EventAction):
    name = "open_shop"
    valid_parameters = [
        (str, "npc_slug"),
    ]

    def start(self):
        npc = get_npc(self.session, self.parameters.npc_slug)

        def buy_menu():
            self.session.client.pop_state()
            self.session.client.push_state(
                "ShopMenuState",
                buyer=self.session.player,
                seller=npc,
            )

        def sell_menu():
            self.session.client.pop_state()
            self.session.client.push_state(
                "ShopMenuState",
                buyer=None,
                seller=self.session.player,
            )

        var_menu = [
            ("Buy", "Buy", buy_menu),
            ("Sell", "Sell", sell_menu),
        ]

        return self.session.client.push_state("ChoiceState", menu=var_menu, escape_key_exits=True)
