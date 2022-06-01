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

from typing import Generator, NamedTuple, Sequence, Tuple, final

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.map import Direction, dirs2
from tuxemon.math import Vector2


def simple_path(
    origin: Tuple[int, int],
    direction: Direction,
    tiles: int,
) -> Generator[Tuple[int, int], None, None]:
    origin_vec = Vector2(origin)
    for _ in range(tiles):
        origin_vec += dirs2[direction]
        yield (int(origin_vec[0]), int(origin_vec[1]))


def parse_path_parameters(
    origin: Tuple[int, int],
    move_list: Sequence[str],
) -> Generator[Tuple[int, int], None, None]:
    for move in move_list:
        try:
            direction, tiles = move.strip().split()
        except ValueError:
            direction, tiles = move.strip(), "1"

        # Pending https://github.com/python/mypy/issues/9718
        assert direction in dirs2
        for point in simple_path(origin, direction, int(tiles)):
            yield point
        origin = point


class NpcMoveActionParameters(NamedTuple):
    pass


@final
class NpcMoveAction(EventAction[NpcMoveActionParameters]):
    """
    Relative tile movement for NPC.

    This action blocks until the destination is reached.


    Script usage:
        .. code-block::

            npc_move <npc_slug>,<move>...

    Script parameters:
        npc_slug: Either "player" or npc slug name (e.g. "npc_maple").
        move: A tuple with format ``<direction> [amount_of_tiles]`` where
            ``direction`` can be one of "up", "down", "left" and "right" and
            ``amount_of_tiles`` is the number of tiles moved in that direction,
            being 1 by default. Several movements can be passed, that will be
            executed one after the other. For example:
            ``up 10, down 5, left 5``.

    """

    name = "npc_move"
    param_class = NpcMoveActionParameters

    # parameter checking not supported due to undefined number of parameters

    def start(self) -> None:
        npc_slug = self.raw_parameters[0]
        self.npc = get_npc(self.session, npc_slug)

        if self.npc is None:
            return

        path = list(parse_path_parameters(
            self.npc.tile_pos,
            self.raw_parameters[1:],
        ))
        path.reverse()
        self.npc.path = path
        self.npc.next_waypoint()

    def update(self) -> None:
        if self.npc is None:
            self.stop()
            return

        if not self.npc.moving and not self.npc.path:
            self.stop()
