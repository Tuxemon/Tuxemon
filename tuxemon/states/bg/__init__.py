# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from typing import Callable

import pygame_menu
from pygame_menu import locals
from pygame_menu.baseimage import POSITION_CENTER

from tuxemon import prepare, tools
from tuxemon.menu.menu import PygameMenuState
from tuxemon.menu.theme import get_theme

logger = logging.getLogger(__name__)


MenuGameObj = Callable[[], object]


class BgState(PygameMenuState):
    """Menu for the change of backgroun"""

    def __init__(self, background: str) -> None:
        width, height = prepare.SCREEN_SIZE
        background = pygame_menu.BaseImage(
            image_path=tools.transform_resource_filename(
                "gfx/ui/background/" + background + ".png"
            ),
            drawing_position=POSITION_CENTER,
        )
        theme = get_theme()
        theme.background_color = background
        theme.widget_alignment = locals.ALIGN_CENTER

        super().__init__(height=height, width=width)
