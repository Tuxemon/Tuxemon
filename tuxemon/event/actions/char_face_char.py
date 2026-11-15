# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.map.map import get_direction, tile_distance
from tuxemon.session import Session


@final
@dataclass
class CharFaceCharAction(EventAction):
    """
    Make an NPC face another character when they come within a specified distance.

    Script usage:
        .. code-block::

    Script parameters:
        npc_slug: Slug of the NPC that will do the turning.
        target_slug: Slug of the character (NPC or player) to look at.
        trigger_dist: Maximum tile distance for the trigger. Defaults to 3.
        persistent: Whether to continue tracking. Defaults to True.
    """

    name = "char_face_char"
    character: str
    target: str
    trigger_dist: int = 3
    persistent: bool = True

    def start(self, session: Session) -> None:
        self.npc = session.client.get_npc(self.character)
        self.target_char = session.client.get_npc(self.target)

    def update(self, session: Session, dt: float) -> None:
        if not self.npc or not self.target_char:
            self.stop()
            return

        dist = tile_distance(self.npc.tile_pos, self.target_char.tile_pos)

        if dist <= self.trigger_dist:
            direction = get_direction(
                self.npc.tile_pos, self.target_char.tile_pos
            )
            self.npc.set_facing(direction)

            if not self.persistent:
                self.stop()
