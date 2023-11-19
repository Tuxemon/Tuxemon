# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from typing import Optional

from tuxemon import prepare
from tuxemon.graphics import string_to_colorlike
from tuxemon.menu.menu import PygameMenuState
from tuxemon.menu.theme import get_theme
from tuxemon.platform.events import PlayerInput


class ColorState(PygameMenuState):
    """
    It imposes a specific color over the world, where
    it'll be possible to dispay dialogues, etc.
    """

    def process_event(self, event: PlayerInput) -> Optional[PlayerInput]:
        return None

    def __init__(self, color: str) -> None:
        width, height = prepare.SCREEN_SIZE
        _color = string_to_colorlike(color)
        theme = get_theme()
        theme.background_color = _color
        super().__init__(height=height, width=width)
