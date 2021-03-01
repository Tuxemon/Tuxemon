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
from tuxemon.core.event.eventaction import EventAction
from tuxemon.core.map import get_direction, dirs2


class NpcFaceAction(EventAction):
    """ Makes the NPC face a certain direction.

    Valid Parameters: npc_slug, direction

    Direction parameter can be: "left", "right", "up", "down", or "player"
    """
    name = "npc_face"
    valid_parameters = [
        (str, "npc_slug"),
        (str, "direction")
    ]

    def start(self):
        npc = get_npc(self.session, self.parameters.npc_slug)
        direction = self.parameters.direction
        if direction not in dirs2:
            if direction == "player":
                target = self.session.player
            else:
                target = get_npc(self.session, direction)
            direction = get_direction(npc.tile_pos, target.tile_pos)

        npc.facing = direction
