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

from tuxemon.core.event.eventcondition import EventCondition


class DialogOpenCondition(EventCondition):
    """ Checks to see if a dialog window is open.
    """
    name = "dialog_open"

    def test(self, session,  condition):
        """ Checks to see if a dialog window is open.

        :param session: The session object
        :param condition: A dictionary of condition details. See :py:func:`core.map.Map.loadevents`
            for the format of the dictionary.

        :type session: tuxemon.core.session.Session
        :type condition: Dictionary

        :rtype: Boolean
        :returns: True or False

        Valid Parameters: None

        **Examples:**

        >>> condition.__dict__
        {
            "type": "dialog_open",
            "parameters": []
            "width": 1,
            "height": 1,
            "operator": "is",
            "x": 2,
            "y": 2,
            ...
        }

        """
        for state in session.client.active_states:
            if state.name == "DialogState":
                return True

        return False
