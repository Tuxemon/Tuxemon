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

from core.components.event.eventcondition import EventCondition


class VariableSetCondition(EventCondition):
    """ Checks to see if a player game variable has been set. This will look for a particular
    key in the player.game_variables dictionary and see if it exists. If it exists, it will
    return true.
    """
    name = "variable_set"

    def test(self, game, condition):
        """ Checks to see if a player game variable has been set. This will look for a particular
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
