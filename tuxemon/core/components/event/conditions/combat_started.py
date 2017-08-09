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


class CombatStartedCondition(EventCondition):
    """ Checks to see if combat has been started or not.
    """
    name = "combat_started"

    def test(self, game, condition):
        """ Checks to see if combat has been started or not.

            :param game: The main game object that contains all the game's variables.
            :param condition: A dictionary of condition details. See :py:func:`core.components.map.Map.loadevents`
                for the format of the dictionary.

            :type game: core.control.Control
            :type condition: Dictionary

            :rtype: Boolean
            :returns: True or False

            Valid Parameters: None

            **Examples:**

            >>> condition
            {'action_id': '9',
             'id': 9,
             'operator': 'is_not',
             'parameters': '',
             'type': 'combat_started',
             'x': 1,
             'y': 11}

            """
        return game.current_state.name == "CombatState"
