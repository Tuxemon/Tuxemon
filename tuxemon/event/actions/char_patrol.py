# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, final

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.map import parse_path_parameters

logger = logging.getLogger(__name__)


@final
@dataclass
class CharPatrolAction(EventAction):
    """
    Enables a character to patrol a predefined route in a continuous loop.

    Script usage:
        .. code-block::

            char_patrol <character>,<move>...

    Parameters:
        character: Either "player" or character slug name (e.g. "npc_maple").
        move: A sequence of movement instructions in the format:
            "<direction> [amount_of_tiles]"
            where:
            - direction: One of "up", "down", "left", "right".
            - amount_of_tiles (optional): Number of tiles to move (default is 1).
            - Multiple moves can be provided, e.g., "up 10, down 5, left 5".

    Functionality:
        - Converts movement instructions into a looping patrol path.
        - NPC moves along the predefined path, restarting when completed.
        - Blocks execution if the NPC encounters an obstacle.
        - Automatically resumes patrol when movement is available.
    """

    name = "char_patrol"
    raw_parameters: Sequence[str] = field(init=False)

    def __init__(self, *args: Any) -> None:
        super().__init__()
        self.raw_parameters = args
        self.patrol_points: list[tuple[int, int]] = field(default_factory=list)
        self.patrol_index: int = 0

    def start(self) -> None:
        if len(self.raw_parameters) < 2:
            logger.error(
                "Insufficient parameters: requires NPC and patrol path"
            )
            return

        npc_name = self.raw_parameters[0]
        move_list = self.raw_parameters[1:]
        self.character = get_npc(self.session, npc_name)

        if not self.character:
            logger.error(f"NPC '{npc_name}' not found")
            return

        try:
            self.patrol_points = list(
                parse_path_parameters(self.character.tile_pos, move_list)
            )
        except Exception as e:
            logger.error(f"Failed to parse patrol path: {e}")
            return

    def update(self) -> None:
        if not self.character or not self.patrol_points:
            self.stop()
            return

        if not self.character.moving and not self.character.path:
            next_pos = self.patrol_points[self.patrol_index]
            self.character.path = [next_pos]
            self.character.next_waypoint()
            self.patrol_index = (self.patrol_index + 1) % len(
                self.patrol_points
            )
