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

from tuxemon.core.db import db
from tuxemon.core.event import get_npc
from tuxemon.core.event.eventaction import EventAction
from tuxemon.core.item.item import decode_inventory


class SetInventoryAction(EventAction):
    """ Overwrites the inventory of the npc or player.
    """
    name = "set_inventory"
    valid_parameters = [
        (str, "npc_slug"),
        ((str, None), "inventory_slug"),
    ]

    def start(self):
        npc = get_npc(self.session, self.parameters.npc_slug)
        if self.parameters.inventory_slug == "None":
            npc.inventory = {}
            return

        entry = db.database["inventory"][self.parameters.inventory_slug]
        npc.inventory = decode_inventory(self.session, npc, entry)
