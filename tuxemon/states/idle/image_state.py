# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from typing import Optional

import pygame_menu
from pygame_menu.locals import POSITION_CENTER

from tuxemon import prepare, tools
from tuxemon.menu.menu import PygameMenuState
from tuxemon.menu.theme import get_theme
from tuxemon.platform.events import PlayerInput


class ImageState(PygameMenuState):
    """
    It imposes an image over the world, where it'll be possible to 
    dispay dialogues, etc.
    """

    def process_event(self, event: PlayerInput) -> Optional[PlayerInput]:
        return None

    def __init__(self, background: str) -> None:
        width, height = prepare.SCREEN_SIZE
        image_path = tools.transform_resource_filename(
            "gfx/ui/background/" + background + ".png"
        )
        theme = get_theme()
        theme.background_color = pygame_menu.BaseImage(
            image_path,
            drawing_position=POSITION_CENTER,
        )
        super().__init__(height=height, width=width)
