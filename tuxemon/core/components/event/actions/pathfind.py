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


class PathfindAction(EventAction):
    """
    Will move the player / npc to the given location
    """
    name = "pathfind"
    valid_parameters = [
        (str, "npc_slug"),
        (int, "tile_pos_x"),
        (int, "tile_pos_y")
    ]

    def start(self):
        # Get a copy of the world state.
        world = self.game.get_state_name("WorldState")
        if not world:
            return

        npc_slug = self.parameters.npc_slug
        dest_x = self.parameters.tile_pos_x
        dest_y = self.parameters.tile_pos_y

        # get npc object via name
        if npc_slug not in world.npcs:
            return

        curr_npc = world.npcs[npc_slug]
        curr_npc.pathfind((dest_x, dest_y), self.game)
