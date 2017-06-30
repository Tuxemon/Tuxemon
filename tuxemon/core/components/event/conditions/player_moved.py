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


class PlayerMovedCondition(EventCondition):
    """ Checks to see where an NPC is facing
    """
    name = "player_moved"

    def test(self, game, condition):
        """Checks to see the player has just moved into this tile. Using this condition will
        prevent a condition like "player_at" from constantly being true every single frame.

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
            "type": "player_moved",
            "parameters": [],
            "width": 1,
            "height": 1,
            "operator": "is",
            "x": 6,
            "y": 9,
            ...
        }

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
