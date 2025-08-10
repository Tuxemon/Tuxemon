# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar, Optional

from pygame_menu.locals import POSITION_EAST

from tuxemon import prepare
from tuxemon.animation import Animation, ScheduleType
from tuxemon.menu.menu import PygameMenuState
from tuxemon.menu.theme import get_theme
from tuxemon.ui.menu_options import MenuOptions


@dataclass
class MenuStateConfig:
    max_elements: int = 13
    max_height_percentage: float = 0.8
    animation_duration: float = 0.2
    animation_start_size: float = 0.0
    animation_end_size: float = 1.0


class ChoiceState(PygameMenuState):
    """
    Game state with a graphic box and some text in it.

    Pressing the action button:
    * if text is being displayed, will cause text speed to go max
    * when text is displayed completely, then will show the next message
    * if there are no more messages, then the dialog will close
    """

    name: ClassVar[str] = "ChoiceState"

    def __init__(
        self,
        menu: MenuOptions,
        escape_key_exits: bool = False,
        config: Optional[MenuStateConfig] = None,
        **kwargs: Any,
    ) -> None:
        self.config = config or MenuStateConfig()
        theme = get_theme().copy()

        if len(menu.options) > self.config.max_elements:
            theme.scrollarea_position = POSITION_EAST

        super().__init__(**kwargs)

        for option in menu.get_menu():
            self.menu.add.button(
                option.display_text,
                option.action,
                font_size=self.font_type.medium,
            )

        self.animation_size = self.config.animation_end_size
        self.escape_key_exits = escape_key_exits

    def update_animation_size(self) -> None:
        widgets_size = self.menu.get_size(widget=True)
        width, height = prepare.SCREEN_SIZE

        _width = widgets_size[0]
        _height = widgets_size[1]

        if _width >= width:
            _width = width
        if _height >= height:
            _height = int(height * self.config.max_height_percentage)

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
        ani = self.animate(
            self,
            animation_size=self.config.animation_end_size,
            duration=self.config.animation_duration,
        )
        ani.schedule(self.update_animation_size, ScheduleType.ON_UPDATE)

        return ani
