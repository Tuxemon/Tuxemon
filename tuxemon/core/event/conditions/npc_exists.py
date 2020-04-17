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

from tuxemon.core.event import get_npc
from tuxemon.core.event.eventcondition import EventCondition


class NPCExistsCondition(EventCondition):
    """ Checks to see if a particular NPC object exists in the current list of NPCs.
    """
    name = "npc_exists"

    def test(self, session,  condition):
        """ Checks to see if a particular NPC object exists in the current list of NPCs.

        :param session: The session object
        :param condition: A dictionary of condition details. See :py:func:`core.map.Map.loadevents`
            for the format of the dictionary.

        :type session: tuxemon.core.session.Session
        :type condition: Dictionary

        :rtype: Boolean
        :returns: True or False

        Valid Parameters: npc_slug

        **Examples:**

        >>> condition.__dict__
        {
            "type": "npc_exists",
            "parameters": [
                "npc_oak"
            ],
            "width": 1,
            "height": 1,
            "operator": "is_not",
            "x": 0,
            "y": 0,
            ...
        }
        """
        if get_npc(session, condition.parameters[0]):
            return True
        else:
            return False
