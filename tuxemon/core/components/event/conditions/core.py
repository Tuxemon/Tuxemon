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

        >>> condition.__dict__
        {
            "type": "button_pressed",
            "parameters": [
                "K_RETURN"
            ],
            "width": 1,
            "height": 1,
            "operator": "is",
            "x": 2,
            "y": 2,
            ...
        }

        """
        # Get the keys pressed from the game.
        events = game.key_events
        button = str(condition.parameters[0])

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

        >>> condition.__dict__
        {
            "type": "button_released",
            "parameters": [
                "K_RETURN"
            ],
            "width": 1,
            "height": 1,
            "operator": "is",
            "x": 2,
            "y": 2,
            ...
        }

        """
        # Get the keys pressed from the game.
        events = game.key_events
        button = str(condition.parameters[0])

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

        >>> condition.__dict__
        {
            "type": "variable_set",
            "parameters": [
                "battle_won:yes"
            ],
            "width": 1,
            "height": 1,
            "operator": "is",
            "x": 2,
            "y": 2,
            ...
        }

        """
        # Get the player object from the game.
        player = game.player1

        # Loop through the player's game variables to see if they have a value that is set.
        for key, value in player.game_variables.items():

            # Split the string by ":" into a list
            var_list = condition.parameters[0].split(":")
            var_key = var_list[0]
            var_value = var_list[1]

            # If the variable is set in the game variables, then we've met the condition.
            if (var_key == key) and (var_value == value):
                return True

        return False


    def dialog_open(self, game, condition):
        """Checks to see if a dialog window is open.

        :param game: The main game object that contains all the game's variables.
        :param condition: A dictionary of condition details. See :py:func:`core.components.map.Map.loadevents`
            for the format of the dictionary.

        :type game: core.control.Control
        :type condition: Dictionary

        :rtype: Boolean
        :returns: True or False

        Valid Parameters: None

        **Examples:**

        >>> condition.__dict__
        {
            "type": "dialog_open",
            "parameters": []
            "width": 1,
            "height": 1,
            "operator": "is",
            "x": 2,
            "y": 2,
            ...
        }

        """
        # Get a copy of the world state.
        world = game.get_state_name("WorldState")
        if not world:
            return False

        if world.dialog_window.visible or len(world.dialog_window.dialog_stack) > 0:
            return True
        else:
            return False
