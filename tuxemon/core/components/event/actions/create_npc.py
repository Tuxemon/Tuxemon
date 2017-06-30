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

from core import prepare
from core.components import ai, player
from core.components.event.eventaction import EventAction


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
        # Get a copy of the world state.
        world = self.game.get_state_name("WorldState")
        if not world:
            return

        # Get the npc's parameters from the action
        slug = self.parameters.npc_slug
        tile_pos_x = self.parameters.tile_pos_x
        tile_pos_y = self.parameters.tile_pos_y
        animations = self.parameters.animations
        behavior = self.parameters.behavior

        # Ensure that the NPC doesn't already exist on the map.
        if slug in world.npcs:
            return

        # Create a new NPC object
        npc = player.Npc(sprite_name=animations, slug=slug)

        # Set the NPC object's variables
        npc.tile_pos = [tile_pos_x, tile_pos_y]
        npc.behavior = behavior
        npc.ai = ai.AI()
        npc.scale_sprites(prepare.SCALE)
        npc.walkrate *= prepare.SCALE
        npc.runrate *= prepare.SCALE
        npc.moverate = npc.walkrate

        # Set the NPC's pixel position based on its tile position, tile size, and
        # current global_x/global_y variables
        npc.position = [(tile_pos_x * world.tile_size[0]) + world.global_x,
                        (tile_pos_y * world.tile_size[1]) + (world.global_y - world.tile_size[1])]

        # Add the NPC to the game's NPC list
        world.npcs[slug] = npc
