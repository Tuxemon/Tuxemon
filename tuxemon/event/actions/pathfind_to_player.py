# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional, final

from tuxemon.db import Direction
from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.map import get_coord_direction, get_coords


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
    direction: Optional[Direction] = None
    distance: Optional[int] = None

    def start(self) -> None:
        player = self.session.player
        client = self.session.client
        self.npc = get_npc(self.session, self.npc_slug)
        assert self.npc

        distance = 1 if self.distance is None else self.distance
        if distance <= 0:
            raise ValueError(f"{distance} cannot be below 0")

        if self.direction is not None:
            closest = get_coord_direction(
                player.tile_pos, self.direction, client.map_size, distance
            )
            self.npc.facing = self.direction
        else:
            target = self.npc.tile_pos
            coords = get_coords(player.tile_pos, client.map_size, distance)
            closest = min(
                coords,
                key=lambda point: math.hypot(
                    target[1] - point[1], target[0] - point[0]
                ),
            )

        self.npc.pathfind(closest)

    def update(self) -> None:
        assert self.npc
        if not self.npc.moving and not self.npc.path:
            self.stop()
