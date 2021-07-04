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

from tuxemon.event.eventcondition import EventCondition


class ButtonReleasedCondition(EventCondition):
    """Checks to see if a particular key was released"""

    name = "button_released"

    def test(self, session, condition):
        """Checks to see if a particular key was released

        :param session: The session object
        :param condition: A dictionary of condition details. See :py:func:`map.Map.loadevents`
            for the format of the dictionary.

        :type session: tuxemon.session.Session
        :type condition: Dictionary

        :rtype: Boolean
        :returns: True or False

        Valid Parameters: A pygame key (E.g. "K_RETURN")
        """
        # no longer in use
        # TODO: Cleanup or remove this action
        raise NotImplementedError
        # # Get the keys pressed from the game.
        # events = game.key_events
        # button = str(condition.parameters[0])
        #
        # # Loop through each event
        # for event in events:
        #     # NOTE: getattr on pygame is a little dangerous. We should sanitize input.
        #     if event.type == pygame.KEYUP and event.key == getattr(pygame, button):
        #         return True

        return False
