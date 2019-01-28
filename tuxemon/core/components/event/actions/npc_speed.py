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
from __future__ import unicode_literals

from tuxemon.core.components.event import get_npc
from tuxemon.core.components.event.eventaction import EventAction


class NpcFaceAction(EventAction):
    """ Makes the NPC face a certain direction.

    Valid Parameters: npc_slug, speed

    Currently not working, limited to walking or running

    Values less than or greater to zero will walk
    Values great than zero will run
    """
    name = "npc_speed"
    valid_parameters = [
        (str, "npc_slug"),
        (float, "speed")
    ]

    def start(self):
        # TODO: finalize how speed values are handled
        npc = get_npc(self.game, self.parameters.npc_slug)
        if self.parameters.speed:
            npc.walking = False
            npc.running = True
        else:
            npc.walking = True
            npc.running = False
