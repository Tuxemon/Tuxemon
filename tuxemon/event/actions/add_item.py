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

from dataclasses import dataclass
from typing import Union, final

from tuxemon.event.eventaction import EventAction


@final
@dataclass
class AddItemAction(EventAction):
    """
    Add an item to the current player's inventory.

    Script usage:
        .. code-block::

            add_item <item_slug>[,quantity]

    Script parameters:
        item_slug: Item name to look up in the item database.
        quantity: Quantity of the item to add. By default it is 1.

    """

    name = "add_item"
    item_slug: str
    quantity: Union[int, None] = None

    def start(self) -> None:
        player = self.session.player
        if self.quantity is None:
            quantity = 1
        else:
            quantity = self.quantity
        player.alter_item_quantity(
            self.session,
            self.item_slug,
            quantity,
        )
