# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, final

from tuxemon.event.eventaction import EventAction
from tuxemon.prepare import TRANS_TIME
from tuxemon.states.world.worldstate import WorldState


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
        world = self.session.client.get_state_by_name(WorldState)

        if world.npcs:
            for _npc in world.npcs:
                if _npc.moving or _npc.path:
                    world.npcs.remove(_npc)

        if world.delayed_teleport:
            self.stop()
            return

        self.session.client.current_music.stop()

        # Start the screen transition
        _time = TRANS_TIME if self.trans_time is None else self.trans_time
        action = self.session.client.event_engine
        self.transition = action.get_action("screen_transition", [_time])

    def update(self) -> None:
        if self.done:
            return

        assert self.transition

        if not self.transition.done:
            self.transition.update()
        else:
            self.transition.cleanup()
            # set the delayed teleport
            action = self.session.client.event_engine
            params = ["player", self.map_name, self.x, self.y]
            action.execute_action("delayed_teleport", params)
            self.stop()
