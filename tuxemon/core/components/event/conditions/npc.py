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

    def _get_npc(self, game, slug):
        """Gets an NPC object by slug.

        :param game: The main game object that contains all the game's variables.
        :param slug: The slug of the NPC that exists on the current map.

        :type game: core.control.Control
        :type slug: Str

        :rtype: core.components.player.Npc
        :returns: The NPC object or None if the NPC is not found.

        """
        # Loop through the NPC list and see if the slug matches any in the list
        world = game.get_state_name("WorldState")
        if not world:
            return

        if slug in world.npcs:
            return world.npcs[slug]

        logger.error("Unable to find NPC: " + slug)
        return


    def npc_exists(self, game, condition):
        """Checks to see if a particular NPC object exists in the current list of NPCs.

        :param game: The main game object that contains all the game's variables.
        :param condition: A dictionary of condition details. See :py:func:`core.components.map.Map.loadevents`
            for the format of the dictionary.

        :type game: core.control.Control
        :type condition: Dictionary

        :rtype: Boolean
        :returns: True or False

        Valid Parameters: npc_slug

        **Examples:**

        >>> condition.__dict__
        {
            "type": "npc_exists",
            "parameters": [
                "npc_oak"
            ],
            "width": 1,
            "height": 1,
            "operator": "is_not",
            "x": 0,
            "y": 0,
            ...
        }

        """
        world = game.get_state_name("WorldState")
        if not world:
            return

        if self._get_npc(game, condition.parameters[0]):
            return True
        else:
            return False


    def npc_at(self, game, condition):
        """Checks to see if an npc is at a current position on the map.

        :param game: The main game object that contains all the game's variables.
        :param condition: A dictionary of condition details. See :py:func:`core.components.map.Map.loadevents`
            for the format of the dictionary.

        :type game: core.control.Control
        :type condition: Dictionary

        :rtype: Boolean
        :returns: True or False

        **Examples:**

        >>> condition.__dict__
        {
            "type": "npc_at",
            "parameters": [
                "npc_maple",
                "6",
                "9"
            ],
            "width": 1,
            "height": 1,
            "operator": "is",
            "x": 6,
            "y": 9,
            ...
        }

        """

        # Get the player object from the game.
        player = self._get_npc(game, condition.parameters[0])
        if not player:
            return False

        # Get the condition's rectangle area. If we're on a tile in that area, then this condition
        # should return True.
        area_x = range(condition.x, condition.x + condition.width)
        area_y = range(condition.y, condition.y + condition.height)

        # If the player is at the coordinates and the operator is set to true then return true
        if round(player.tile_pos[0]) in area_x and round(player.tile_pos[1]) in area_y:
            return True

        # If the player is at the coordinates and the operator is set to false then return false
        else:
            return False


    def npc_facing(self, game, condition):
        """Checks to see where an NPC is facing

        :param game: The main game object that contains all the game's variables.
        :param condition: A dictionary of condition details. See :py:func:`core.map.Map.loadevents`
            for the format of the dictionary.

        :type game: core.control.Control
        :type condition: Dictionary

        :rtype: Boolean
        :returns: True or False

        Valid Parameters: npc_slug, direction ("up", "down", "left" or "right")

        **Examples:**

        >>> condition.__dict__
        {
            "type": "npc_facing",
            "parameters": [
                "npc_maple",
                "up"
            ],
            "width": 1,
            "height": 1,
            "operator": "is",
            "x": 6,
            "y": 9,
            ...
        }

        """
        # Get the player object from the game.
        player = self._get_npc(game, condition.parameters[0])
        if not player:
            return False
        facing = condition.parameters[1]

        if player.facing == facing:
            return True
        else:
            return False


    def npc_facing_tile(self, game, condition):
        """Checks to see if an NPC is facing a tile position

        :param game: The main game object that contains all the game's variables.
        :param condition: A dictionary of condition details. See :py:func:`core.components.map.Map.loadevents`
            for the format of the dictionary.

        :type game: core.control.Control
        :type condition: Dictionary

        :rtype: Boolean
        :returns: True or False

        **Examples:**

        >>> condition.__dict__
        {
            "type": "facing_tile",
            "parameters": ["npc_maple"],
            "width": 1,
            "height": 1,
            "operator": "is",
            "x": 6,
            "y": 9,
            ...
        }

        """
        # Get the player object from the game.
        player = self._get_npc(game, condition.parameters[0])
        if not player:
            return False

        coordinates = (condition.x, condition.y)
        tile_location = None

        # Next, we check the player position and see if we're one tile away from
        # the tile.
        if coordinates[1] == player.tile_pos[1]:
            # Check to see if the tile is to the left of the player
            if coordinates[0] == player.tile_pos[0] - 1:
                logger.debug("Tile is to the left of the NPC")
                tile_location = "left"
            # Check to see if the tile is to the right of the player
            elif coordinates[0] == player.tile_pos[0] + 1:
                logger.debug("Tile is to the right of the player")
                tile_location = "right"

        if coordinates[0] == player.tile_pos[0]:
            # Check to see if the tile is above the player
            if coordinates[1] == player.tile_pos[1] - 1:
                logger.debug("Tile is above the player")
                tile_location = "up"
            elif coordinates[1] == player.tile_pos[1] + 1:
                logger.debug("Tile is below the player")
                tile_location = "down"

        # Then we check to see if we're facing the Tile
        if player.facing == tile_location:
            return True
        else:
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

        Valid Parameters: slug

        **Examples:**

        >>> condition.__dict__
        {
            "type": "facing_npc",
            "parameters": [
                "npc_oak"
            ],
            "width": 1,
            "height": 1,
            "operator": "is",
            "x": 0,
            "y": 0,
            ...
        }

        """
        npc_location = None

        world = game.current_state
        npc = self._get_npc(condition.parameters[0])
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
