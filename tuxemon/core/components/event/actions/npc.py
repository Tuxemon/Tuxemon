#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Tuxemon
# Copyright (C) 2014, William Edwards <shadowapex@gmail.com>
#
# This file is part of Tuxemon.
#
# Tuxemon is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Tuxemon is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Tuxemon.  If not, see <http://www.gnu.org/licenses/>.
#
# Contributor(s):
#
# William Edwards <shadowapex@gmail.com>
#

class Npc(object):

    def create_npc(self, game, action):
        """Creates an NPC object and adds it to the game's current list of NPC's.

        :param game: The main game object that contains all the game's variables.
        :param action: The action (tuple) retrieved from the database that contains the action's
            parameters

        :type game: core.control.Control
        :type action: Tuple

        :rtype: None
        :returns: None

        Valid Parameters: name,tile_pos_x,tile_pos_y,animations,behavior

        **Examples:**

        >>> action
        ('create_npc', 'Oak,1,5,oak,wander', '1', 6)

        """

        ai = game.imports["ai"]
        player = game.imports["player"]

        # Get a copy of the world state.
        world = game.get_world_state()
        if not world: 
            return

        # Get the npc's parameters from the action
        parameters = action[1].split(",")
        name = str(parameters[0])
        tile_pos_x = int(parameters[1])
        tile_pos_y = int(parameters[2])
        animations = str(parameters[3])
        behavior = str(parameters[4])

        # Create a new NPC object
        npc = player.Npc(sprite_name=animations, name=name)

        # Set the NPC object's variables
        npc.tile_pos = [tile_pos_x, tile_pos_y]
        npc.behavior = behavior
        npc.ai = ai.AI()
        npc.scale_sprites(world.scale)
        npc.walkrate *= world.scale
        npc.runrate *=world.scale
        npc.moverate = npc.walkrate

        # Set the NPC's pixel position based on its tile position, tile size, and
        # current global_x/global_y variables
        npc.position = [(tile_pos_x * world.tile_size[0]) + world.global_x,
                        (tile_pos_y * world.tile_size[1]) + (world.global_y - world.tile_size[1])]


        # Add the NPC to the game's NPC list
        world.npcs.append(npc)
        return npc

    def pathfind(self, game, action):
        '''
        Will move the player / npc to the given location
        '''
        # Get a copy of the world state.
        world = game.world

        print("action is " + str(action))
        parameters = action[1].split(",")
        npc_name = parameters[0]
        dest_x = parameters[1]
        dest_y = parameters[2]

        # get npc object via name
        curr_npc = None
        for n in world.npcs:
            if n.name == npc_name:
                curr_npc = n
                print("found npc: " +npc_name)

        curr_npc.pathfind((int(dest_x),int(dest_y)), game)

