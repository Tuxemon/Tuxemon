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

from core.components.event.conditions import get_npc
from core.components.event.eventcondition import EventCondition


class NPCFacingCondition(EventCondition):
    """ Checks to see where an NPC is facing
    """
    name = "npc_facing"

    def test(self, game, condition):
        """ Checks to see where an NPC is facing

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
        player = get_npc(game, condition.parameters[0])
        if not player:
            return False
        facing = condition.parameters[1]

        if player.facing == facing:
            return True
        else:
            return False
