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

from yapsy.IPlugin import IPlugin
from core.components import ai
from core.components import player


class Npc(IPlugin):

    def create_npc(self, game, action):
        """Creates an NPC object and adds it to the game's current list of NPC's.
    
        :param game: The main game object that contains all the game's variables.
        :param action: The action (tuple) retrieved from the database that contains the action's
            parameters
    
        :type game: core.tools.Control
        :type action: Tuple
    
        :rtype: None
        :returns: None
    
        Valid Parameters: name,tile_pos_x,tile_pos_y,animations,behavior
            
        **Examples:**
    
        >>> action
        ('create_npc', 'Oak,1,5,oak,wander', '1', 6)
    
        """
    
        # Get a copy of the world state.
        world = game.state_dict["WORLD"]
    
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
    
        # Set the NPC's pixel position based on its tile position, tile size, and
        # current global_x/global_y variables
        npc.position = [(tile_pos_x * world.tile_size[0]) + world.global_x,
                        (tile_pos_y * world.tile_size[1]) + world.global_y]
    
            
        # Add the NPC to the game's NPC list
        world.npcs.append(npc)
    
    
