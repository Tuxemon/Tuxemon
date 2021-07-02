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

from __future__ import annotations
from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from typing import NamedTuple, final


class PathfindActionParameters(NamedTuple):
    npc_slug: str
    tile_pos_x: int
    tile_pos_y: int


@final
class PathfindAction(EventAction[PathfindActionParameters]):
    """Pathfind the player / npc to the given location

    This action blocks until the destination is reached.

    Valid Parameters: npc_slug, tile_pos_x, tile_pos_y
    """

    name = "pathfind"
    param_class = PathfindActionParameters

    def start(self) -> None:
        self.npc = get_npc(self.session, self.parameters.npc_slug)
        self.npc.pathfind((self.parameters.tile_pos_x, self.parameters.tile_pos_y))

    def update(self) -> None:
        if not self.npc.moving and not self.npc.path:
            self.stop()
