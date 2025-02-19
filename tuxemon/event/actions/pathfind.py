# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import final

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction


@final
@dataclass
class PathfindAction(EventAction):
    """
    Pathfind the player / npc to the given location.

    This action blocks until the destination is reached.

    Script usage:
        .. code-block::

            pathfind <npc_slug>

    Script parameters:
        npc_slug: Either "player" or npc slug name (e.g. "npc_maple").

    """

    name = "pathfind"
    npc_slug: str
    tile_pos_x: int
    tile_pos_y: int

    def start(self) -> None:
        self.npc = get_npc(self.session, self.npc_slug)
        assert self.npc
        self.npc.pathfind((self.tile_pos_x, self.tile_pos_y))

    def update(self) -> None:
        assert self.npc
        if not self.npc.moving and not self.npc.path:
            self.stop()
