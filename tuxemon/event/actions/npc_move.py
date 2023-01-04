# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generator, Sequence, Tuple, cast, final

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
        direction = cast(Direction, direction)
        for point in simple_path(origin, direction, int(tiles)):
            yield point
        origin = point


@final
@dataclass
class NpcMoveAction(EventAction):
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
    raw_parameters: Sequence[str] = field(init=False)

    def __init__(self, *args):
        super().__init__()
        self.raw_parameters = args

    # parameter checking not supported due to undefined number of parameters

    def start(self) -> None:
        npc_slug = self.raw_parameters[0]
        self.npc = get_npc(self.session, npc_slug)

        if self.npc is None:
            return

        path = list(
            parse_path_parameters(
                self.npc.tile_pos,
                self.raw_parameters[1:],
            )
        )
        path.reverse()
        self.npc.path = path
        self.npc.next_waypoint()

    def update(self) -> None:
        if self.npc is None:
            self.stop()
            return

        if not self.npc.moving and not self.npc.path:
            self.stop()
