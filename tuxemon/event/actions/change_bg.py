# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, final

from pygame_menu import locals

from tuxemon.event.eventaction import EventAction
from tuxemon.menu.menu import BACKGROUND_COLOR
from tuxemon.menu.theme import get_theme
from tuxemon.states.idle.color_state import ColorState
from tuxemon.states.idle.image_state import ImageState


@final
@dataclass
class ChangeBgAction(EventAction):
    """
    Change the background.

    Eg:
    act1 change_bg background
    act2 change_bg

    Script usage:
        .. code-block::

            change_bg <background>

    Script parameters:
        background:
        - it can be the name of the file (see below note)
        - it can be a RGB color separated by ":" (eg 255:0:0)

        note: the files must be inside the folder (gfx/ui/background/)
        Size: 240x160

    """

    name = "change_bg"
    background: Optional[str] = None

    def start(self) -> None:
        # don't override previous state if we are still in the state.
        current_state = self.session.client.current_state
        if current_state is None:
            # obligatory "should not happen"
            raise RuntimeError

        # this function cleans up the previous state without crashing
        if len(self.session.client.state_manager.active_states) > 2:
            self.session.client.pop_state()

        if current_state.name != str(ImageState):
            if self.background is None:
                self.session.client.pop_state()
                return
            else:
                _background = self.background.split(":")
                if len(_background) == 1:
                    self.session.client.push_state(
                        ImageState(background=self.background)
                    )
                else:
                    self.session.client.push_state(
                        ColorState(color=self.background)
                    )

    def cleanup(self) -> None:
        theme = get_theme()
        theme.background_color = BACKGROUND_COLOR
        theme.widget_alignment = locals.ALIGN_LEFT
