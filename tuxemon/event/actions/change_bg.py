# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import final

from pygame_menu import locals

from tuxemon.event.eventaction import EventAction
from tuxemon.menu.menu import BACKGROUND_COLOR
from tuxemon.menu.theme import get_theme
from tuxemon.states.bg import BgState


@final
@dataclass
class ChangeBgAction(EventAction):
    """
    Change the background.

    It's advisable end the bg sequence with "end"

    Eg:
    act1 change_bg filename
    act2 change_bg end

    Script usage:
        .. code-block::

            change_bg <background>

    Script parameters:
        background: The name of the file without .PNG

        the files must be inside the folder (gfx/ui/background/)
        Size: 240x160

    """

    name = "change_bg"
    background: str

    def start(self) -> None:
        # don't override previous state if we are still in the state.
        current_state = self.session.client.current_state
        if current_state is None:
            # obligatory "should not happen"
            raise RuntimeError

        # this function cleans up the previous state without crashing
        if len(self.session.client.state_manager.active_states) > 2:
            self.session.client.pop_state()

        if current_state.name != BgState:
            if self.background == "end":
                return
            else:
                self.session.client.push_state(
                    BgState(background=self.background)
                )

    def cleanup(self) -> None:
        theme = get_theme()
        theme.background_color = BACKGROUND_COLOR
        theme.widget_alignment = locals.ALIGN_LEFT
