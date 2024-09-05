# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Generator, Sequence
from dataclasses import dataclass, field
from typing import Any, final

from tuxemon.db import Direction
from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.map import dirs2
from tuxemon.math import Vector2

logger = logging.getLogger(__name__)


def simple_path(
    origin: tuple[int, int],
    direction: Direction,
    tiles: int,
) -> Generator[tuple[int, int], None, None]:
    """Generate a simple path in the given direction from the origin."""
    origin_vec = Vector2(origin)
    for _ in range(tiles):
        origin_vec += dirs2[direction]
        yield (int(origin_vec.x), int(origin_vec.y))


def parse_path_parameters(
    origin: tuple[int, int],
    move_list: Sequence[str],
) -> Generator[tuple[int, int], None, None]:
    """Parse a list of move commands and generate the corresponding path."""
    for move in move_list:
        try:
            direction, tiles = move.strip().split()
        except ValueError:
            direction, tiles = move.strip(), "1"
        direction = Direction(direction)
        for point in simple_path(origin, direction, int(tiles)):
            yield point
        origin = point


@final
@dataclass
class CharMoveAction(EventAction):
    """
    Relative tile movement for character.

    This action blocks until the destination is reached.


    Script usage:
        .. code-block::

            char_move <character>,<move>...

    Script parameters:
        character: Either "player" or character slug name (e.g. "npc_maple").
        move: A tuple with format ``<direction> [amount_of_tiles]`` where
            ``direction`` can be one of "up", "down", "left" and "right" and
            ``amount_of_tiles`` is the number of tiles moved in that direction,
            being 1 by default. Several movements can be passed, that will be
            executed one after the other. For example:
            ``up 10, down 5, left 5``.

    """

    name = "char_move"
    raw_parameters: Sequence[str] = field(init=False)

    def __init__(self, *args: Any) -> None:
        super().__init__()
        self.raw_parameters = args

    # parameter checking not supported due to undefined number of parameters

    def start(self) -> None:
        if len(self.raw_parameters) < 2:
            logger.error("Insufficient parameters")
            return

        character_name = self.raw_parameters[0]
        self.character = get_npc(self.session, character_name)

        if self.character is None:
            logger.error(f"Character '{character_name}' not found")
            return

        path_parameters = self.raw_parameters[1:]
        try:
            path = list(
                parse_path_parameters(self.character.tile_pos, path_parameters)
            )
        except Exception as e:
            logger.error(f"Failed to parse path parameters: {e}")
            return

        if path:
            path.reverse()
            self.character.path = path
            self.character.next_waypoint()
        else:
            logger.error("No path found")

    def update(self) -> None:
        if self.character is None:
            self.stop()
            return

        if not self.character.moving and not self.character.path:
            self.stop()
