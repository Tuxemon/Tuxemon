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


class NpcMoveAction(EventAction):
    """ Makes the move to a tile location

    This action blocks until the destination is reached.

    Valid Parameters: npc_slug,

    Direction parameter can be: "left", "right", "up", or "down"
    """
    name = "npc_move"
    valid_parameters = [
        (str, "npc_slug"),
        (int, "pos_x"),
        (int, "pos_y"),
        (int, "speed")
    ]

    def start(self):
        print(self.parameters)
        npc = get_npc(self.game, self.parameters.npc_slug)
        # npc.move_to((self.parameters.pos_x, self.parameters.pos_y), self.parameters.speed)
        world_map = self.game.get_state_name("WorldState")
        npc.pathfind((self.parameters.pos_x, self.parameters.pos_y), world_map)
