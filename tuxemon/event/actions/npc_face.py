# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import final

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.map import dirs2, get_direction
from tuxemon.npc import NPC


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
    direction: str  # Using Direction as the typehint breaks the Action

    def start(self) -> None:
        npc = get_npc(self.session, self.npc_slug)
        assert npc
        direction = self.direction

        target: NPC
        if direction not in dirs2:
            if direction == "player":
                target = self.session.player
            else:
                maybe_target = get_npc(self.session, direction)
                assert maybe_target
                target = maybe_target
            direction = get_direction(npc.tile_pos, target.tile_pos)

        npc.facing = direction
