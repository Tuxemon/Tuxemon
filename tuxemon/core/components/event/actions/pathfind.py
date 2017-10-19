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

from core.components.event import get_npc
from core.components.event.eventaction import EventAction


class PathfindAction(EventAction):
    """ Pathfind the player / npc to the given location

    This action blocks until the destination is reached.

    Valid Parameters: npc_slug, pos_x, pos_y
    """
    name = "pathfind"
    valid_parameters = [
        (str, "npc_slug"),
        (int, "pos_x"),
        (int, "pos_y"),
    ]

    def start(self):
        destination = self.parameters.pos_x, self.parameters.pos_y
        self.npc = get_npc(self.game, self.parameters.npc_slug)
        self.npc.pathfind(destination)
        self.npc.moveConductor.play()

    def update(self):
        if not self.npc.moving and not self.npc.path:
            self.stop()
            self.npc.moveConductor.stop()
