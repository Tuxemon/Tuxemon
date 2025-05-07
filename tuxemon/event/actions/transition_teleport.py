# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, final

from tuxemon.event.eventaction import EventAction
from tuxemon.graphics import ColorLike, string_to_colorlike
from tuxemon.prepare import BLACK_COLOR, TRANS_TIME, fetch
from tuxemon.states.world.worldstate import WorldState
from tuxemon.teleporter import DelayedTeleport


@final
@dataclass
class TransitionTeleportAction(EventAction):
    """
    Combines the "teleport" and "screen_transition" actions.

    Perform a teleport with a screen transition. Useful for allowing the player
    to go to different maps.

    Script usage:
        .. code-block::

            transition_teleport <map_name>,<x>,<y>[,trans_time][,rgb]

    Script parameters:
        map_name: Name of the map to teleport to.
        x: X coordinate of the map to teleport to.
        y: Y coordinate of the map to teleport to.
        trans_time: Transition time in seconds - default 0.3
        rgb: color (eg red > 255,0,0 > 255:0:0) - default rgb(0,0,0)

    """

    name = "transition_teleport"
    map_name: str
    x: int
    y: int
    trans_time: Optional[float] = None
    rgb: Optional[str] = None

    def start(self) -> None:
        self.world = self.session.client.get_state_by_name(WorldState)
        delayed_teleport = self.world.teleporter.delayed_teleport

        target_map = fetch("maps", self.map_name)

        if self.world.npcs and self.world.current_map.filename != target_map:
            self.world.npcs = [
                npc for npc in self.world.npcs if not (npc.moving or npc.path)
            ]

        if delayed_teleport.is_active:
            self.stop()
            return

        self.session.client.current_music.stop()

        # Start the screen transition
        _time = TRANS_TIME if self.trans_time is None else self.trans_time
        rgb: ColorLike = BLACK_COLOR
        if self.rgb:
            rgb = string_to_colorlike(self.rgb)
        self.setup_delayed_teleport(delayed_teleport)
        self.world.transition_manager.fade_and_teleport(
            _time,
            rgb,
            lambda: self.world.teleporter.handle_delayed_teleport(
                self.world.player
            ),
        )

    def update(self) -> None:
        if self.done:
            return

    def setup_delayed_teleport(self, delayed: DelayedTeleport) -> None:
        """Configure delayed teleport after the screen transition."""
        delayed.char = None
        delayed.is_active = True
        delayed.mapname = self.map_name
        delayed.x = self.x
        delayed.y = self.y
        self.stop()
