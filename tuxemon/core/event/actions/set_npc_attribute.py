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

from tuxemon.core.event import get_npc
from tuxemon.core.event.actions.common import CommonAction
from tuxemon.core.event.eventaction import EventAction


class SetNpcAttributeAction(EventAction):
    """ Sets the given attribute of the npc to the given value.

    Valid Parameters: slug, attribute, value

    **Example:**

    >>> action.__dict__
    {
        "type": "set_npc_attribute",
        "parameters": [
            "npc_maple"
            "party_limit",
            "8"
        ]
    }
    """
    name = "set_npc_attribute"
    valid_parameters = [
        (str, "npc_slug"),
        (str, "name"),
        (str, "value")
    ]

    def start(self):
        npc = get_npc(self.session, self.parameters[0])
        attribute = self.parameters[1]
        value = self.parameters[2]
        CommonAction.set_character_attribute(npc, attribute, value)
