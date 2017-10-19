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

import core.components.npc
from core.components import ai, player
from core.components.event.eventaction import EventAction


class CreateNpcAction(EventAction):
    """Creates an NPC object and adds it to the game's current list of NPC's.

    Valid Parameters: slug, tile_pos_x, tile_pos_y, animations, behavior
    """
    name = "create_npc"
    valid_parameters = [
        (str, "npc_slug"),
        (int, "pos_x"),
        (int, "pos_y"),
        (str, "animations"),
        (str, "behavior")
    ]

    def start(self):
        # Get a copy of the world state.
        world = self.game.get_state_name("WorldState")
        if not world:
            return

        # Get the npc's parameters from the action
        slug = self.parameters.npc_slug

        # Get the npc's parameters from the action
        pos_x = self.parameters.pos_x
        pos_y = self.parameters.pos_y
        behavior = self.parameters.behavior

        # Create a new NPC object
        npc = core.components.npc.Npc(slug)
        npc.set_position((pos_x, pos_y))

        # Set the NPC object's variables
        npc.behavior = behavior
        npc.ai = ai.AI()

        print('new!!!', npc, pos_x, pos_y, npc.tile_pos)
        # Add the NPC to the game's NPC list
        world.add_entity(npc)
