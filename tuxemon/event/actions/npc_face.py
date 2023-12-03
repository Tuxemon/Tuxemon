# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import final

from tuxemon.db import Direction
from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.map import get_direction


@final
@dataclass
class NpcFaceAction(EventAction):
    """
    Make the NPC face a certain direction.

    Script usage:
        .. code-block::

            npc_face <npc_slug>,<direction>

    Script parameters:
        npc_slug: Either "player" or npc slug name (e.g. "npc_maple").
        direction: Direction to face. It can be: "left", "right", "up", "down",
             "player" or a npc slug.

    """

    name = "npc_face"
    npc_slug: str
    direction: str

    def start(self) -> None:
        npc = get_npc(self.session, self.npc_slug)
        assert npc

        # "player" isn't among the Directions (map_loader.py)
        if self.direction not in list(Direction):
            target = get_npc(self.session, self.direction)
            assert target
            direction = get_direction(npc.tile_pos, target.tile_pos)
        else:
            direction = Direction(self.direction)

        npc.facing = direction
