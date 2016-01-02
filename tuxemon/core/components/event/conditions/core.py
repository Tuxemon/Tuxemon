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

import pygame

class Core(object):

    def true(self, game, condition):
        """This function always returns true unless the operator is set to "is_not"

        :param game: The main game object that contains all the game's variables.
        :param condition: A dictionary of condition details. See :py:func:`core.components.map.Map.loadevents`
            for the format of the dictionary.

        :type game: core.control.Control
        :type condition: Dictionary

        :rtype: Boolean
        :returns: True or False

        """

        return True


    def button_pressed(self, game, condition):
        """Checks to see if a particular key was pressed

        :param game: The main game object that contains all the game's variables.
        :param condition: A dictionary of condition details. See :py:func:`core.components.map.Map.loadevents`
            for the format of the dictionary.

        :type game: core.control.Control
        :type condition: Dictionary

        :rtype: Boolean
        :returns: True or False

        Valid Parameters: A pygame key (E.g. "K_RETURN")

        **Examples:**

        >>> condition
        {'action_id': '3',
         'id': 3,
         'operator': 'is',
         'parameters': 'K_RETURN',
         'type': 'button_pressed',
         'x': 1,
         'y': 3}

        """

        # Get the keys pressed from the game.
        events = game.key_events
        button = str(condition["parameters"])

        # Loop through each event
        for event in events:
            # NOTE: getattr on pygame is a little dangerous. We should sanitize input.
            if event.type == pygame.KEYDOWN and event.key == getattr(pygame, button):
                return True

        return False


    def button_released(self, game, condition):
        """Checks to see if a particular key was released

        :param game: The main game object that contains all the game's variables.
        :param condition: A dictionary of condition details. See :py:func:`core.components.map.Map.loadevents`
            for the format of the dictionary.

        :type game: core.control.Control
        :type condition: Dictionary

        :rtype: Boolean
        :returns: True or False

        Valid Parameters: A pygame key (E.g. "K_RETURN")

        **Examples:**

        >>> condition
        {'action_id': '3',
         'id': 3,
         'operator': 'is',
         'parameters': 'K_RETURN',
         'type': 'button_released',
         'x': 1,
         'y': 3}

        """

        # Get the keys pressed from the game.
        events = game.key_events
        button = str(condition["parameters"])

        # Loop through each event
        for event in events:
            # NOTE: getattr on pygame is a little dangerous. We should sanitize input.
            if event.type == pygame.KEYUP and event.key == getattr(pygame, button):
                return True

        return False


    def variable_set(self, game, condition):
        """Checks to see if a player game variable has been set. This will look for a particular
        key in the player.game_variables dictionary and see if it exists. If it exists, it will
        return true.

        :param game: The main game object that contains all the game's variables.
        :param condition: A dictionary of condition details. See :py:func:`core.components.map.Map.loadevents`
            for the format of the dictionary.

        :type game: core.control.Control
        :type condition: Dictionary

        :rtype: Boolean
        :returns: True or False

        Valid Parameters: variable_name:value

        **Examples:**

        >>> condition
        {'action_id': '20',
         'id': 2,
         'operator': 'is',
         'parameters': 'battle_won:yes',
         'type': 'variable_set',
         'x': 0,
         'y': 0}

        """

        # Get the player object from the game.
        player = game.player1

        # Loop through the player's game variables to see if they have a value that is set.
        for key, value in player.game_variables.items():

            # Split the string by ":" into a list
            varlist = condition["parameters"].split(":")
            varkey = varlist[0]
            varvalue = varlist[1]

            # If the variable is set in the game variables, then we've met the condition.
            if (varkey == key) and (varvalue == value):
                return True

        return False

