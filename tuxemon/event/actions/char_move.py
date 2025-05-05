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
class CharMoveAction(EventAction):
    """
    Relative tile movement for characters.

    It interprets movement instructions, updates character positions accordingly,
    and blocks execution until the destination is reached.

    Script usage:
        .. code-block::

            char_move <character>,<move>...

    Script parameters:
        character: Either "player" or character slug name (e.g. "npc_maple").
        move: A sequence of movement instructions in the format:
            "<direction> [amount_of_tiles]"
            where:
            - direction: One of "up", "down", "left", "right".
            - amount_of_tiles (optional): Number of tiles to move (default is 1).
            - Multiple moves can be provided, e.g., "up 10, down 5, left 5".
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
        except ValueError as e:
            logger.error(
                f"Failed to parse path parameters due to invalid input: {e}"
            )
            return

        if path:
            path.reverse()
            self.character.path = path
            self.character.next_waypoint()
        else:
            logger.error("No valid path was generated")

    def update(self) -> None:
        if self.character is None:
            self.stop()
            return

        if not self.character.moving and not self.character.path:
            self.stop()
