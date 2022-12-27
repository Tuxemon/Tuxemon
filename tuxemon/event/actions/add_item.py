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
from typing import Optional, Union, final

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.npc import NPC


@final
@dataclass
class AddItemAction(EventAction):
    """
    Add an item to the specified trainer's inventory.

    Script usage:
        .. code-block::

            add_item <item_slug>[,quantity][,trainer_slug]

    Script parameters:
        item_slug: Item name to look up in the item database.
        quantity: Quantity of the item to add. By default it is 1.
        trainer_slug: Slug of the trainer that will receive the item. It
            defaults to the current player.

    """

    name = "add_item"
    item_slug: str
    quantity: Union[int, None] = None
    trainer_slug: str = None

    def start(self) -> None:
        trainer: Optional[NPC]

        if self.trainer_slug is None:
            trainer = self.session.player
        else:
            trainer = get_npc(self.session, self.trainer_slug)

        assert trainer, "No Trainer found with slug '{}'".format(
            self.trainer_slug or "player"
        )
        if self.quantity is None:
            quantity = 1
        else:
            quantity = self.quantity

        trainer.alter_item_quantity(
            self.session,
            self.item_slug,
            quantity,
        )
