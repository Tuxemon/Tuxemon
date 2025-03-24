# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from functools import partial
from typing import Optional, final

from tuxemon.event.eventaction import EventAction
from tuxemon.graphics import ColorLike, string_to_colorlike
from tuxemon.prepare import BLACK_COLOR, TRANS_TIME
from tuxemon.states.world.worldstate import WorldState


@final
@dataclass
class ScreenTransitionAction(EventAction):
    """
    Initiate a screen transition.

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
    trans_time: Optional[float] = None
    rgb: Optional[str] = None

    def start(self) -> None:
        pass

    def update(self) -> None:
        world = self.session.client.get_state_by_name(WorldState)
        _time = TRANS_TIME if self.trans_time is None else self.trans_time
        rgb: ColorLike = BLACK_COLOR
        if self.rgb:
            rgb = string_to_colorlike(self.rgb)

        if not world.in_transition:
            self.fade_and_teleport(world, _time, rgb)
            self.stop()

    def fade_and_teleport(
        self, world: WorldState, duration: float, color: ColorLike
    ) -> None:
        """
        Fade out, teleport, fade in.

        Parameters:
            duration: Duration of the fade out. The fade in is slightly larger.
            color: Fade's color.

        """

        def cleanup() -> None:
            world.set_transition_state(False)

        def fade_in() -> None:
            world.fade_in(duration, color)
            world.task(cleanup, duration)

        # cancel any fades that may be going one
        world.remove_animations_of(world)
        world.remove_animations_of(cleanup)

        world.stop_and_reset_char(world.player)

        world.set_transition_state(True)
        world.fade_out(duration, color)

        task = world.task(
            partial(world.teleporter.handle_delayed_teleport, world.player),
            duration,
        )
        task.chain(fade_in, duration + 0.5)
