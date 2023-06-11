# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import final

from pygame_menu import locals

from tuxemon.event.eventaction import EventAction
from tuxemon.menu.menu import BACKGROUND_COLOR
from tuxemon.menu.theme import get_theme
from tuxemon.states.loading import LoadingState


@final
@dataclass
class LoadingScreenAction(EventAction):
    """
    Block event chain for some time and change background.

    Script usage:
        .. code-block::

            loading_screen <seconds>,<background>

    Script parameters:
        seconds: Time in seconds for the event engine to wait for.
        background: The name of the file without .PNG

        the files must be inside the folder (gfx/ui/background/)
        Size: 240x160

    """

    name = "loading_screen"
    seconds: float
    background: str

    # TODO: use event loop time, not wall clock
    def start(self) -> None:
        self.client = self.session.client
        self.finish_time = time.time() + self.seconds
        # don't override previous state if we are still in the state.
        self.current = self.client.current_state
        if self.current is None:
            # obligatory "should not happen"
            raise RuntimeError

        if len(self.client.state_manager.active_states) > 2:
            self.client.pop_state()

        if self.current.name != str(LoadingState):
            self.client.push_state(LoadingState(background=self.background))

    def update(self) -> None:
        if time.time() >= self.finish_time:
            self.stop()
            self.client.pop_state()

    def cleanup(self) -> None:
        theme = get_theme()
        theme.background_color = BACKGROUND_COLOR
        theme.widget_alignment = locals.ALIGN_LEFT
