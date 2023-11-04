# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, final

from tuxemon.event.eventaction import EventAction
from tuxemon.graphics import ColorLike, string_to_colorlike
from tuxemon.states.world.worldstate import WorldState


@final
@dataclass
class ScreenTransitionAction(EventAction):
    """
    Initiate a screen transition.

    Script usage:
        .. code-block::

            screen_transition [transition_time][,rgb]

    Script parameters:
        transition_time: Transition time in seconds - default 2
        rgb: color (eg red > 255,0,0 > 255:0:0) - default rgb(0,0,0)

    eg: "screen_transition 3"
    eg: "screen_transition 3,255:0:0:50" (red)

    """

    name = "screen_transition"
    transition_time: Optional[float] = None
    rgb: Optional[str] = None

    def start(self) -> None:
        pass

    def update(self) -> None:
        world = self.session.client.get_state_by_name(WorldState)
        if not self.transition_time:
            self.transition_time = 2.0
        rgb: ColorLike = (0, 0, 0)
        if self.rgb:
            rgb = string_to_colorlike(self.rgb)

        if not world.in_transition:
            if self.rgb:
                world.fade_and_teleport(self.transition_time, rgb)
            else:
                world.fade_and_teleport(self.transition_time, rgb)
            self.stop()
