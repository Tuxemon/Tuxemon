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
from tuxemon.states.world_state import WorldState


@final
@dataclass
class ScreenTransitionAction(EventAction):
    """
    Initiate a screen transition that blocks until both fade out and fade in
    are complete.

    Script usage:
        .. code-block::

            screen_transition [trans_time][,rgb]

    Script parameters:
        trans_time: Transition time in seconds - default 0.3
        rgb: color (eg red > 255,0,0 > 255:0:0) - default rgb(0,0,0)

    eg: "screen_transition 3"
    eg: "screen_transition 3,255:0:0:50" (red)
    """

    name = "screen_transition"
    trans_time: float | None = None
    rgb: str | None = None
    elapsed: float = 0.0

    def start(self, session: Session) -> None:
        self._fade_in_triggered = False
        world = session.client.get_state_by_name(WorldState)
        self._time = TRANS_TIME if self.trans_time is None else self.trans_time
        self._rgb: ColorLike = BLACK_COLOR
        if self.rgb:
            self._rgb = string_to_colorlike(self.rgb)

        world.transition_manager.fade_out(self._time, self._rgb)
        self.elapsed = 0.0

    def update(self, session: Session, dt: float) -> None:
        self.elapsed += dt
        world = session.client.get_state_by_name(WorldState)

        if self.elapsed >= self._time and not self._fade_in_triggered:
            world.transition_manager.fade_in(self._time, self._rgb)
            self._fade_in_triggered = True

        if self.elapsed >= 2 * self._time:
            self.stop()
