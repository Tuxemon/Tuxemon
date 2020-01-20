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
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging

from tuxemon.core import monster
from tuxemon.core.event.eventcondition import EventCondition

logger = logging.getLogger(__name__)


class PartyLevelCondition(EventCondition):
    """ Checks to see where an NPC is facing
    """
    name = "party_level"

    def test(self, game, condition):
        """Perform various checks about the player's party size. With this condition you can see if
        the player's party is less than, greater than, or equal to then number you specify.

        :param game: The main game object that contains all the game's variables.
        :param condition: A dictionary of condition details. See :py:func:`core.map.Map.loadevents`
            for the format of the dictionary.

        :type game: core.control.Control
        :type condition: Dictionary

        :rtype: Boolean
        :returns: True or False

        Valid Parameters: check, level

        The "check" parameter can be one of the following: "average", "lowest", or "highest".
        """
        check = str(condition.parameters[0])
        level = int(condition.parameters[1])

        """
        player = game.player1
        for monster in player.monsters:
            
        """
        if len(game.player1.monsters) == 0:
            return False

        level_lowest = monster.MAX_LEVEL
        level_highest = 0
        level_average = 0
        for monster in game.player1.monsters:
            if monster.level < level_lowest:
                level_lowest = monster.level
            if monster.level > level_highest:
                level_highest = monster.level
            level_average += monster.level
        level_average = int(round(level_average / len(game.player1.monsters)))

        # Check to see if the party's average level is beyond this level.
        if check == "average":
            return level_average >= level

        # Check to see if the party's lowest level monster has reached this level.
        elif check == "lowest":
            return level_lowest >= level

        # Check to see if the party's highest level monster has reached this level.
        elif check == "highest":
            return level_highest >= level

        else:
            raise Exception("Party level check parameters are incorrect.")

        return False
