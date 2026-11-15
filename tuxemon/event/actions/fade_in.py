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
class FadeInAction(EventAction):
    """
    Fade in and block until the fade duration has completed.

    Script usage:
        .. code-block::

            fade_in [trans_time][,rgb]

    Script parameters:
        trans_time: Transition time in seconds - default 0.3
        rgb: color (eg red > 255,0,0 > 255:0:0) - default rgb(0,0,0)

    eg: "fade_in 3"
    eg: "fade_in 3,255:0:0:50" (red)
    """

    name = "fade_in"
    trans_time: float | None = None
    rgb: str | None = None
    elapsed: float = 0.0

    def start(self, session: Session) -> None:
        world = session.client.get_state_by_name(WorldState)
        self._time = TRANS_TIME if self.trans_time is None else self.trans_time
        self._rgb: ColorLike = BLACK_COLOR
        if self.rgb:
            self._rgb = string_to_colorlike(self.rgb)

        world.transition_manager.fade_in(self._time, self._rgb)
        self.elapsed = 0.0

    def update(self, session: Session, dt: float) -> None:
        self.elapsed += dt
        if self.elapsed >= self._time:
            self.stop()
