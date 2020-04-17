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

from tuxemon.core.event import MapCondition
from tuxemon.core.event.conditions.button_pressed import ButtonPressedCondition
from tuxemon.core.event.conditions.player_facing_npc import PlayerFacingNPCCondition
from tuxemon.core.event.eventcondition import EventCondition


class ToTalkCondition(EventCondition):
    """ Checks if we are attempting to talk to an npc
    """
    name = "to_talk"

    def test(self, session,  condition):
        """ Checks to see the player is next to and facing a particular NPC and that the Return button is pressed.

        :param session: The session object
        :param condition: The condition details.

        :type session: tuxemon.core.session.Session
        :type condition: NamedTuple

        :rtype: Boolean
        :returns: True or False

        Valid Parameters: npc slug

        **Examples:**

        condition.__dict__ = {
            "type": "to_talk",
            "parameters": [
                "npc_oak"
            ],
            "width": 1,
            "height": 1,
            "operator": "is",
            "x": 0,
            "y": 0,
            ...
        }
        """
        player_next_to_and_facing_target = PlayerFacingNPCCondition().test(session, condition)
        button_pressed = ButtonPressedCondition().test(
            session,
            MapCondition(
                type="button_pressed",
                parameters=[
                    "K_RETURN",
                ],
                operator="is",
                width=0,
                height=0,
                x=0,
                y=0,
                name="",
            )
        )
        return player_next_to_and_facing_target and button_pressed

