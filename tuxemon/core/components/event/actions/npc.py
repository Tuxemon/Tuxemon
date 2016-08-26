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
from __future__ import absolute_import

from collections import namedtuple
from core import prepare
from core.components import ai
from core.components import player
from core.components.event import Condition


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

        Valid Parameters: slug,tile_pos_x,tile_pos_y,animations,behavior

        **Examples:**

        >>> action.__dict__
        {
            "type": "create_npc",
            "parameters": [
                "npc_oak",
                "1",
                "5",
                "oak",
                "wander"
            ]
        }

        """
        # Get a copy of the world state.
        world = game.get_state_name("WorldState")
        if not world:
            return

        # Get the npc's parameters from the action
        slug = str(action.parameters[0])
        tile_pos_x = int(action.parameters[1])
        tile_pos_y = int(action.parameters[2])
        animations = str(action.parameters[3])
        behavior = str(action.parameters[4])

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
        return npc

    def remove_npc(self, game, action):
        """Removes an NPC object from the list of NPCs.

        :param game: The main game object that contains all the game's variables.
        :param action: The action (tuple) retrieved from the database that contains the action's
            parameters

        :type game: core.control.Control
        :type action: Tuple

        :rtype: None
        :returns: None

        Valid Parameters: slug

        **Examples:**

        >>> action.__dict__
        {
            "type": "remove_npc",
            "parameters": [
                "npc_oak"
            ]
        }

        """
        # Get a copy of the world state.
        world = game.get_state_name("WorldState")
        if not world:
            return

        # Get the npc's parameters from the action
        slug = str(action.parameters[0])

        if slug not in world.npcs:
            return

        # Create a separate list of NPCs to loop through
        del world.npcs[slug]


    def npc_face(self, game, action):
        """Makes the NPC face a certain direction.

        :param game: The main game object that contains all the game's variables.
        :param action: The action (tuple) retrieved from the database that contains the action's
            parameters

        :type game: core.control.Control
        :type action: Tuple

        :rtype: None
        :returns: None

        Valid Parameters: npc_slug, direction

        Action parameter can be: "left", "right", "up", or "down"
        **Examples:**

        >>> action.__dict__
        {
            "type": "npc_face",
            "parameters": [
                "npc_oak",
                "left"
            ]
        }
        """

        # Get the parameters to determine what direction the player will face.
        slug = action.parameters[0]
        direction = action.parameters[1]

        event_engine = game.event_engine
        npc = event_engine.conditions["_get_npc"]["method"](game, slug)
        if not npc:
            return

        npc.facing = direction


    def pathfind(self, game, action):
        '''
        Will move the player / npc to the given location
        '''
        # Get a copy of the world state.
        world = game.get_state_name("WorldState")
        if not world:
            return

        npc_slug = action.parameters[0]
        dest_x = action.parameters[1]
        dest_y = action.parameters[2]

        # get npc object via name
        if npc_slug not in world.npcs:
            return

        curr_npc = world.npcs[npc_slug]
        curr_npc.pathfind((int(dest_x),int(dest_y)), game)
