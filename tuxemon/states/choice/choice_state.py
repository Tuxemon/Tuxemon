# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from pygame_menu.locals import POSITION_EAST

from tuxemon import prepare
from tuxemon.animation import Animation
from tuxemon.menu.menu import PygameMenuState
from tuxemon.menu.theme import get_theme

ChoiceMenuGameObj = Callable[[], None]
MAX_MENU_ELEMENTS = 13
MAX_MENU_HEIGHT_PERCENTAGE = 0.8
ANIMATION_DURATION = 0.2
ANIMATION_SIZE = 1.0


class ChoiceState(PygameMenuState):
    """
    Game state with a graphic box and some text in it.

    Pressing the action button:
    * if text is being displayed, will cause text speed to go max
    * when text is displayed completely, then will show the next message
    * if there are no more messages, then the dialog will close
    """

    def __init__(
        self,
        menu: Sequence[tuple[str, str, Callable[[], None]]] = (),
        escape_key_exits: bool = False,
        **kwargs: Any,
    ) -> None:
        theme = get_theme()
        if len(menu) > MAX_MENU_ELEMENTS:
            theme.scrollarea_position = POSITION_EAST

        super().__init__(**kwargs)

        for _, label, callback in menu:
            self.menu.add.button(label, callback, font_size=self.font_size)

        self.animation_size = 0.0
        self.escape_key_exits = escape_key_exits

    def update_animation_size(self) -> None:
        widgets_size = self.menu.get_size(widget=True)
        width, height = prepare.SCREEN_SIZE

        _width = widgets_size[0]
        _height = widgets_size[1]

        if _width >= width:
            _width = width
        if _height >= height:
            _height = int(height * MAX_MENU_HEIGHT_PERCENTAGE)

        self.menu.resize(
            max(1, int(_width * self.animation_size)),
            max(1, int(_height * self.animation_size)),
        )

    def animate_open(self) -> Animation:
        """
        Animate the menu popping in.

        Returns:
            Popping in animation.

        """
        self.animation_size = 0.0

        ani = self.animate(
            self, animation_size=ANIMATION_SIZE, duration=ANIMATION_DURATION
        )
        ani.update_callback = self.update_animation_size

        return ani
