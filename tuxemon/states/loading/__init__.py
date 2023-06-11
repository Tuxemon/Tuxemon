# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from typing import Callable, List

import pygame_menu
from pygame_menu import locals
from pygame_menu.locals import POSITION_CENTER

from tuxemon import prepare, tools
from tuxemon.locale import T
from tuxemon.menu.menu import PygameMenuState
from tuxemon.menu.theme import get_theme

MenuGameObj = Callable[[], object]


def fix_height(screen_y: int, pos_y: float) -> int:
    """it returns the correct height based on percentage"""
    value = round(screen_y * pos_y)
    return value


class LoadingState(PygameMenuState):
    """Menu for for changing background"""

    def __init__(self, background: str) -> None:
        width, height = prepare.SCREEN_SIZE

        # random choice cathedral ads
        if background == "cathedral_ads":
            ads = random.randint(1, 8)
            background = f"cathedral_ads_{ads}"

        image_path = tools.transform_resource_filename(
            f"gfx/ui/background/{background}.png"
        )
        theme = get_theme()
        theme.background_color = pygame_menu.BaseImage(
            image_path,
            drawing_position=POSITION_CENTER,
        )
        theme.widget_alignment = locals.ALIGN_CENTER

        super().__init__(height=height, width=width)

        self.menu._width = fix_height(self.menu._width, 0.95)
        msg = T.translate(background)
        label = self.menu.add.label(
            title=msg,
            label_id=background,
            font_size=20,
            background_color=(192, 192, 192),
            float=True,
            wordwrap=True,
        )
        assert not isinstance(label, List)
        label.translate(0, fix_height(height, 0.35))
