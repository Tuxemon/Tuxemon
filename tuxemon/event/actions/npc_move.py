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
from tuxemon.map import dirs2
from typing import NamedTuple, final, Sequence


def simple_path(origin, direction, tiles):
    origin = tuple(origin)  # make copy to prevent modifying the npc
    for i in range(tiles):
        origin += dirs2[direction]
        yield tuple(int(i) for i in origin)


def parse_path_parameters(
    origin,
    move_list: Sequence[str],
):
    for move in move_list:
        try:
            direction, tiles = move.strip().split()
        except ValueError:
            direction, tiles = move.strip(), 1
        for point in simple_path(origin, direction, int(tiles)):
            yield point
        origin = point


class NpcMoveActionParameters(NamedTuple):
    pass


@final
class NpcMoveAction(EventAction[NpcMoveActionParameters]):
    """Relative tile movement for NPC

    This action blocks until the destination is reached.

    npc_move npc_slug, direction, amount_of_tiles, ...

    number of tiles is optional, defaults to 1 if omitted

    for example: up 10, down 5, left 5

    Direction parameter can be: "left", "right", "up", or "down"

    Valid Parameters: npc_slug, movement pairs
    """

    name = "npc_move"
    param_class = NpcMoveActionParameters

    # parameter checking not supported due to undefined number of parameters

    def start(self) -> None:
        npc_slug = self.raw_parameters[0]
        self.npc = get_npc(self.session, npc_slug)

        if self.npc is None:
            return

        path = list(parse_path_parameters(self.npc.tile_pos, self.raw_parameters[1:]))
        path.reverse()
        self.npc.path = path
        self.npc.next_waypoint()

    def update(self) -> None:
        if self.npc is None:
            self.stop()
            return

        if not self.npc.moving and not self.npc.path:
            self.stop()
