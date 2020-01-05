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

from tuxemon.core.components.event.eventcondition import EventCondition
from tuxemon.core.platform.const import intentions


class ButtonPressedCondition(EventCondition):
    """ Checks to see if a particular key was pressed
    """
    name = "button_pressed"

    def test(self, game, condition):
        """ Checks to see if a particular key was pressed

        :param game: The main game object that contains all the game's variables.
        :param condition: A dictionary of condition details. See :py:func:`core.components.map.Map.loadevents`
            for the format of the dictionary.

        :type game: core.control.Control
        :type condition: Dictionary

        :rtype: Boolean
        :returns: True or False

        Valid Parameters: A button/intention key (E.g. "INTERACT")
        """
        button = str(condition.parameters[0])

        # TODO: workaround for old maps.  eventually need to decide on a scheme and fix existing scripts
        if button == "K_RETURN":
            button = intentions.INTERACT
        else:
            raise ValueError("Cannot support key type: {}".format(button))

        # Loop through each event
        for event in game.key_events:
            if event.pressed and event.button == button:
                return True

        return False
