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
from tuxemon.event.eventaction import EventAction
from typing import Union, NamedTuple, final


class AddItemActionParameters(NamedTuple):
    item_slug: str
    quantity: Union[int, None]


@final
class AddItemAction(EventAction[AddItemActionParameters]):
    """
    Adds an item to the current player's inventory.

    The action parameter must contain an item name to look up in the item
    database.
    """

    name = "add_item"
    param_class = AddItemActionParameters

    def start(self) -> None:
        player = self.session.player
        if self.parameters.quantity is None:
            quantity = 1
        else:
            quantity = self.parameters.quantity
        player.alter_item_quantity(self.session, self.parameters.item_slug, quantity)
