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

from tuxemon.core.event import MapCondition
from tuxemon.core.event.conditions.button_pressed import ButtonPressedCondition
from tuxemon.core.event.conditions.player_facing_npc import PlayerFacingNPCCondition
from tuxemon.core.event.eventcondition import EventCondition


class ToTalkCondition(EventCondition):
    """ Checks if we are attempting to talk to an npc
    """

    name = "to_talk"

    def test(self, context, event, condition):
        """ Checks to see the player is next to and facing a particular NPC and that the Return button is pressed.

        :param event:
        :param context: The session object
        :param condition: The condition details.

        :type context: tuxemon.core.session.Session
        :type condition: NamedTuple

        :rtype: Boolean
        :returns: True or False

        Valid Parameters: npc slug

        """
        player_next_to_and_facing_target = PlayerFacingNPCCondition().test(context, event, condition)
        button_pressed = ButtonPressedCondition().test(context, event,
                                                       MapCondition(name="button_pressed", operator="is",
                                                                    parameters=["K_RETURN", ], ))
        return player_next_to_and_facing_target and button_pressed
