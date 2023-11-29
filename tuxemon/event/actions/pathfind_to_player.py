# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Union, final

from tuxemon.db import Direction
from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction


@final
@dataclass
class PathfindToPlayerAction(EventAction):
    """
    Pathfind npc close the player.

    Script usage:
        .. code-block::

            pathfind_to_player <npc_slug>,[direction],[distance]

    Script parameters:
        npc_slug: Npc slug name (e.g. "npc_maple").
        direction: Approaches the player from up, down, left or right.
        distance: How many tiles (2, 3, 4, etc.)

    """

    name = "pathfind_to_player"
    npc_slug: str
    side: Union[Direction, None] = None
    distance: Union[int, None] = None

    def start(self) -> None:
        self.npc = get_npc(self.session, self.npc_slug)
        assert self.npc
        x, y = self.session.player.tile_pos
        if self.distance is None:
            value = 1
        else:
            if self.distance == 0:
                raise ValueError(
                    f"{self.distance} cannot be 0 (player coordinates).",
                )
            else:
                value = self.distance
        if self.side is not None:
            self.tile_pos_x = 0
            self.tile_pos_y = 0
            if self.side == Direction.up:
                closest = (x, y - value)
                self.npc.facing = self.side
            elif self.side == Direction.down:
                closest = (x, y + value)
                self.npc.facing = self.side
            elif self.side == Direction.right:
                closest = (x + value, y)
                self.npc.facing = self.side
            elif self.side == Direction.left:
                closest = (x - value, y)
                self.npc.facing = self.side
            else:
                raise ValueError(
                    f"{self.side} must be up, down, left or right.",
                )
        else:
            target = self.npc.tile_pos
            destination = [
                (x, y - value),
                (x, y + value),
                (x + value, y),
                (x - value, y),
            ]
            closest = min(
                destination,
                key=lambda point: math.hypot(
                    target[1] - point[1], target[0] - point[0]
                ),
            )
        self.npc.pathfind(closest)

    def update(self) -> None:
        assert self.npc
        if not self.npc.moving and not self.npc.path:
            self.stop()
