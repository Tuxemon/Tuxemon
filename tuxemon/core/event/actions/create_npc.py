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

import logging

import tuxemon.core.npc
from tuxemon.core.event import get_npc
from tuxemon.core.event.eventaction import EventAction

logger = logging.getLogger(__name__)


class CreateNpcAction(EventAction):
    """Creates an NPC object and adds it to the game's current list of NPC's.

    Valid Parameters: slug, tile_pos_x, tile_pos_y, animations, behavior
    """
    name = "create_npc"
    valid_parameters = [
        (str, "npc_slug"),
        (int, "tile_pos_x"),
        (int, "tile_pos_y"),
        (str, "animations"),
        (str, "behavior")
    ]

    def start(self):
        slug = self.parameters.npc_slug

        # Ensure that the NPC doesn't already exist
        if get_npc(self.session, slug) is not None:
            return

        # Create a new NPC object
        pos_x = self.parameters.tile_pos_x
        pos_y = self.parameters.tile_pos_y
        npc = tuxemon.core.npc.NPC(slug)
        npc.set_position((pos_x, pos_y))

        # TODO: Get the map name from the event
        npc.map_name = self.session.player.map_name
        self.session.world.add_entity(npc)
