# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.graphics import ColorLike, string_to_colorlike
from tuxemon.platform.const.graphics import BLACK_COLOR
from tuxemon.platform.const.sizes import TRANS_TIME
from tuxemon.session import Session
from tuxemon.teleporter import TeleportRequest


@final
@dataclass
class TransitionTeleportAction(EventAction):
    """
    Combines the "teleport" and "screen_transition" actions.

    Perform a teleport with a screen transition. Useful for allowing the player
    to go to different maps.

    Script usage:
        .. code-block::

            transition_teleport <character>,<map_name>,<x>,<y>[,trans_time][,rgb]

    Script parameters:
        character: Slug of the character to teleport.
        map_name: Name of the map to teleport to.
        x: X coordinate of the map to teleport to.
        y: Y coordinate of the map to teleport to.
        trans_time: (Optional) Transition time in seconds. Default is 0.3.
        rgb: (Optional) Transition color in RGB format (e.g. "255:0:0" for red).
             Default is black (0,0,0).
    """

    name = "transition_teleport"
    character: str
    map_name: str
    x: int
    y: int
    trans_time: float | None = None
    rgb: str | None = None

    def start(self, session: Session) -> None:

        char = session.client.get_npc(self.character)
        if char is None:
            self.stop()
            return

        teleport_queue = session.client.teleporter.teleport_queue

        if not teleport_queue.is_empty():
            self.stop()
            return

        _time = TRANS_TIME if self.trans_time is None else self.trans_time
        rgb: ColorLike = BLACK_COLOR
        if self.rgb:
            rgb = string_to_colorlike(self.rgb)

        request = TeleportRequest(
            char=None,
            mapname=self.map_name,
            x=self.x,
            y=self.y,
            facing=None,
            source_map=char.current_map,
            source_x=char.tile_pos[0],
            source_y=char.tile_pos[1],
        )
        teleport_queue.enqueue(request)

        session.world.prepare_for_teleport()
        session.world.transition_manager.fade_and_teleport(
            _time,
            rgb,
            char,
            lambda: session.client.teleporter.handle_next_teleport(char),
        )

        self.stop()
