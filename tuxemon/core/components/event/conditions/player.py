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
from yapsy.IPlugin import IPlugin

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)


class Player(IPlugin):

    def player_at(self, game, condition):
        """Checks to see if the player is at a current position on the map.
    
        :param game: The main game object that contains all the game's variables.
        :param condition: A dictionary of condition details. See :py:func:`core.components.map.Map.loadevents`
            for the format of the dictionary. 
    
        :type game: core.tools.Control
        :type condition: Dictionary
    
        :rtype: Boolean
        :returns: True or False 
    
        **Examples:**
    
        >>> condition
        {'action_id': '11',
         'id': 11,
         'operator': 'is',
         'parameters': '6,9',
         'type': 'player_at',
         'x': 6,
         'y': 9,
         'width': 1,
         'height': 1}
    
        """
    
        # Get the player object from the game.
        player = game.player1
    
        # Get the condition's coordinates in tuple format
        coordinates = (condition['x'], condition['y'])
    
        # Get the condition's rectangle area. If we're on a tile in that area, then this condition
        # should return True.
        area_x = range(condition['x'], condition['x'] + condition['width'])
        area_y = range(condition['y'], condition['y'] + condition['height'])
    
        # If the player is at the coordinates and the operator is set to true then return true
        if round(player.tile_pos[0]) in area_x and round(player.tile_pos[1]) in area_y:
            return True
    
        # If the player is at the coordinates and the operator is set to false then return false    
        else:
            return False
    
    
    def player_facing(self, game, condition):
        """Checks to see where the player is facing
    
        :param game: The main game object that contains all the game's variables.
        :param condition: A dictionary of condition details. See :py:func:`core.map.Map.loadevents`
            for the format of the dictionary. 
    
        :type game: core.tools.Control
        :type condition: Dictionary
    
        :rtype: Boolean
        :returns: True or False
    
        Valid Parameters: direction ("up", "down", "left" or "right")
    
        **Examples:**
           
        >>> condition
        {'action_id': '3',
         'id': 3,
         'operator': 'is',
         'parameters': 'up',
         'type': 'player_facing',
         'x': 1,
         'y': 3}
    
        """
    
        # Get the player object from the game.
        player = game.player1
        facing = condition["parameters"]
    
        if player.facing == facing:
            return True
        else:
            return False
    
    
    def player_moved(self, game, condition):
        """Checks to see the player has just moved into this tile. Using this condition will
        prevent a condition like "player_at" from constantly being true every single frame.
    
        :param game: The main game object that contains all the game's variables.
        :param condition: A dictionary of condition details. See :py:func:`core.components.map.Map.loadevents`
            for the format of the dictionary. 
    
        :type game: core.tools.Control
        :type condition: Dictionary
    
        :rtype: Boolean
        :returns: True or False 
    
        Valid Parameters: None
            
        **Examples:**
    
        >>> condition
        {'action_id': '7',
         'id': 7,
         'operator': 'is',
         'parameters': '',
         'type': 'player_moved',
         'x': 0,
         'y': 0}
    
        """
    
        # Create a dictionary that will hold our move destinations.
        if 'move_destination' not in game.event_persist:
            game.event_persist['move_destination'] = {}
    
        if str(condition) not in game.event_persist['move_destination']:
            game.event_persist['move_destination'][str(condition)] = game.player1.move_destination
    
        # Check to see if the player's "move destination" has changed since the last
        # frame. If it has, WE'RE MOVING!
        moved = False
        if game.player1.move_destination == game.event_persist['move_destination'][str(condition)]:
            moved = False
        else:
            moved = True
    
        # Update the current player's last move destination.
        game.event_persist['move_destination'][str(condition)] = game.player1.move_destination
    
        # Check for "is" or "is_not" in the condition.
        if moved:
            return True
        else:
            return False
    
    
    def party_size(self, game, condition):
        """Perform various checks about the player's party size. With this condition you can see if
        the player's party is less than, greater than, or equal to then number you specify.
    
        :param game: The main game object that contains all the game's variables.
        :param condition: A dictionary of condition details. See :py:func:`core.components.map.Map.loadevents`
            for the format of the dictionary. 
    
        :type game: core.tools.Control
        :type condition: Dictionary
    
        :rtype: Boolean
        :returns: True or False 
    
        Valid Parameters: check,party_size
    
        The "check" parameter can be one of the following: "equals", "less_than", or "greater_than".
    
        **Examples:**
    
        >>> condition
        {'action_id': '7',
         'id': 7,
         'type': 'party_size',
         'operator': 'is',
         'parameters': 'less_than,2',
         'x': 0,
         'y': 0}
    
        """
    
        parameters = condition['parameters'].split(',')
        check = str(parameters[0])
        number = int(parameters[1])
        party_size = len(game.player1.monsters)
    
        # Check to see if the player's party size equals this number.
        if check == "equals":
            logger.debug("Equal check")
            if party_size == number:
                return True
            else:
                return False
    
        # Check to see if the player's party size is LESS than this number.
        elif check == "less_than":
            if party_size < number:
                return True
            else:
                return False
    
        # Check to see if the player's part size is GREATER than this number.
        elif check == "greater_than":
            if party_size > number:
                return True
            else:
                return False
    
        else:
            raise Exception("Party size check parameters are incorrect.")
    
        return False
    
