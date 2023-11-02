# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, final

from tuxemon.event.actions.delayed_teleport import DelayedTeleportAction
from tuxemon.event.actions.screen_transition import ScreenTransitionAction
from tuxemon.event.eventaction import EventAction
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

            transition_teleport <map_name>,<x>,<y>[,transition_time][,rgb]

    Script parameters:
        map_name: Name of the map to teleport to.
        x: X coordinate of the map to teleport to.
        y: Y coordinate of the map to teleport to.
        transition_time: Transition time in seconds - default 2
        rgb: color (eg red > 255,0,0 > 255:0:0) - default rgb(0,0,0)

    """

    name = "transition_teleport"
    map_name: str
    x: int
    y: int
    transition_time: Optional[float] = None
    rgb: Optional[str] = None

    def start(self) -> None:
        world = self.session.client.get_state_by_name(WorldState)
        if world.delayed_teleport:
            self.stop()
            return

        # Start the screen transition
        self.transition = ScreenTransitionAction(
            transition_time=self.transition_time, rgb=self.rgb
        )
        self.transition.start()

    def update(self) -> None:
        if self.done:
            return

        assert self.transition

        if not self.transition.done:
            self.transition.update()
        if self.transition.done:
            self.transition.cleanup()
            # set the delayed teleport
            DelayedTeleportAction(
                map_name=self.map_name, position_x=self.x, position_y=self.y
            ).start()
            self.stop()
