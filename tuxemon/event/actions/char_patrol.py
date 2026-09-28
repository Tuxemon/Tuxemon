# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, final

from tuxemon.entity.behavior.base import PatrolBehavior
from tuxemon.event.eventaction import EventAction
from tuxemon.map.map import parse_path_parameters
from tuxemon.session import Session

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

    def start(self, session: Session) -> None:
        if len(self.raw_parameters) < 2:
            logger.error(
                "Insufficient parameters: requires NPC and patrol path"
            )
            self.stop()
            return

        npc_name = self.raw_parameters[0]
        move_list = self.raw_parameters[1:]
        npc = session.client.get_npc(npc_name)

        if not npc:
            logger.error(f"NPC '{npc_name}' not found")
            self.stop()
            return

        try:
            route = list(parse_path_parameters(npc.tile_pos, move_list))
        except Exception as e:
            logger.error(f"Failed to parse patrol path: {e}")
            self.stop()
            return

        # Assign PatrolBehavior
        npc.behavior_policy = PatrolBehavior(route)
