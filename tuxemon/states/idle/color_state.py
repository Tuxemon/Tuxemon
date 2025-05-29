# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from typing import Optional

from tuxemon import prepare
from tuxemon.graphics import string_to_colorlike
from tuxemon.menu.menu import PygameMenuState
from tuxemon.menu.theme import get_theme
from tuxemon.platform.events import PlayerInput


class ColorState(PygameMenuState):
    """
    A state that overlays a solid color over the game world, allowing for
    dialogues, menus, or other UI elements to be displayed.
    """

    def process_event(self, event: PlayerInput) -> Optional[PlayerInput]:
        return None

    def __init__(self, color: str) -> None:
        width, height = prepare.SCREEN_SIZE
        _color = string_to_colorlike(color)
        theme = get_theme()
        if isinstance(_color, tuple) and len(_color) in (3, 4):
            theme.background_color = _color
        else:
            raise ValueError("Invalid color format for background_color")
        super().__init__(height=height, width=width)
