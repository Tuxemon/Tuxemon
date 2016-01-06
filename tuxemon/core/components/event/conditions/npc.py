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

import logging

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)


class Npc(object):

    def npc_exists(self, game, condition):
        """Checks to see if a particular NPC object exists in the current list of NPCs.

        :param game: The main game object that contains all the game's variables.
        :param condition: A dictionary of condition details. See :py:func:`core.components.map.Map.loadevents`
            for the format of the dictionary.

        :type game: core.control.Control
        :type condition: Dictionary

        :rtype: Boolean
        :returns: True or False

        Valid Parameters: npc_name

        **Examples:**

        >>> condition.__dict__
        {
            "type": "npc_exists",
            "parameters": [
                "Oak"
            ],
            "width": 1,
            "height": 1,
            "operator": "is_not",
            "x": 0,
            "y": 0,
            ...
        }

        """
        # Loop through the NPC list and see if the name matches any in the list
        world = game.get_state_name("world")
        if not world:
            return

        for npc in world.npcs:
            if npc.name == condition.parameters[0]:
                return True

        return False


    def facing_npc(self, game, condition):
        """Checks to see the player is next to and facing a particular NPC

        :param game: The main game object that contains all the game's variables.
        :param condition: A dictionary of condition details. See :py:func:`core.components.map.Map.loadevents`
            for the format of the dictionary.

        :type game: core.control.Control
        :type condition: Dictionary

        :rtype: Boolean
        :returns: True or False

        Valid Parameters: npc_name

        **Examples:**

        >>> condition.__dict__
        {
            "type": "facing_npc",
            "parameters": [
                "Oak"
            ],
            "width": 1,
            "height": 1,
            "operator": "is",
            "x": 0,
            "y": 0,
            ...
        }

        """
        npc_name = condition.parameters[0]
        npc_location = None

        # First, find the NPC by name
        world = game.current_state
        for item in world.npcs:
            if item.name == npc_name:
                npc = item      # We found the NPC!

        # If we couldn't find the NPC, return false as we're not next to it :P
        if not npc:
            return False

        # Next, we check the player position and see if we're one tile away from the NPC.
        if npc.tile_pos[1] == game.player1.tile_pos[1]:
            # Check to see if the NPC is to the left of the player
            if npc.tile_pos[0] == game.player1.tile_pos[0] - 1:
                logger.debug("NPC is to the left of the player")
                npc_location = "left"
            # Check to see if the NPC is to the right of the player
            elif npc.tile_pos[0] == game.player1.tile_pos[0] + 1:
                logger.debug("NPC is to the right of the player")
                npc_location = "right"

        if npc.tile_pos[0] == game.player1.tile_pos[0]:
            # Check to see if the NPC is above the player
            if npc.tile_pos[1] == game.player1.tile_pos[1] - 1:
                logger.debug("NPC is above the player")
                npc_location = "up"
            elif npc.tile_pos[1] == game.player1.tile_pos[1] + 1:
                logger.debug("NPC is below the player")
                npc_location = "down"

        # Then we check to see if we're facing the NPC
        if game.player1.facing == npc_location:
            return True
        else:
            return False
