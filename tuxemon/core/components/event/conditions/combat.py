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


class Combat(object):

    def combat_started(self, game, condition):
        """Checks to see if combat has been started or not.

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
        world = game.current_state
        if (game.state_name == "CombatState"
            or world.battle_transition_in_progress
            or world.start_battle_transition
            or world.next == "CombatState"):
            return True
        else:
            return False



