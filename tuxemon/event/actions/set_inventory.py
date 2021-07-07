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
from tuxemon.db import db
from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.item.item import decode_inventory
from typing import NamedTuple, Union, final


class SetInventoryActionParameters(NamedTuple):
    npc_slug: str
    inventory_slug: Union[str, None]


@final
class SetInventoryAction(EventAction[SetInventoryActionParameters]):
    """Overwrites the inventory of the npc or player."""

    name = "set_inventory"
    param_class = SetInventoryActionParameters

    def start(self) -> None:
        npc = get_npc(self.session, self.parameters.npc_slug)
        if self.parameters.inventory_slug == "None":
            npc.inventory = {}
            return

        entry = db.database["inventory"][self.parameters.inventory_slug].get("inventory", {})
        npc.inventory = decode_inventory(self.session, npc, entry)
