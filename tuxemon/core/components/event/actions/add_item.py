# -*- coding: utf-8 -*-
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
from __future__ import absolute_import

from core.components.event.eventaction import EventAction
from core.components.item import Item


class AddItemAction(EventAction):
    """ Adds an item to the current player's inventory.

    The action parameter must contain an item name to look up in the item database.
    """
    name = "add_item"
    valid_parameters = [
        (str, "item_slug")
    ]

    def start(self):
        player = self.game.player1
        item_to_add = Item(self.parameters.item_slug)

        # If the item already exists in the player's inventory, add to its quantity, otherwise
        # just add the item.
        if item_to_add.slug in player.inventory:
            player.inventory[item_to_add.slug]['quantity'] += 1
        else:
            player.inventory[item_to_add.slug] = {'item': item_to_add, 'quantity': 1}
