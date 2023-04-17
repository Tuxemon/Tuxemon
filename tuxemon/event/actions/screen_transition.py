# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.states.world.worldstate import WorldState


@final
@dataclass
class ScreenTransitionAction(EventAction):
    """
    Initiate a screen transition.

    Script usage:
        .. code-block::

            screen_transition <transition_time>

    Script parameters:
        transition_time: Transition time in seconds.

    """

    name = "screen_transition"
    transition_time: float

    def start(self) -> None:
        pass

    def update(self) -> None:
        world = self.session.client.get_state_by_name(WorldState)

        if not world.in_transition:
            world.fade_and_teleport(self.transition_time)
            self.stop()
