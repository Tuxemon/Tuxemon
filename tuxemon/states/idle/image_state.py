# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from typing import Optional

import pygame_menu
from pygame_menu.locals import ALIGN_CENTER, POSITION_CENTER

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

    def __init__(self, background: str, image: Optional[str] = None) -> None:
        width, height = prepare.SCREEN_SIZE
        image_path = tools.transform_resource_filename(
            "gfx/ui/background/" + background + ".png"
        )
        theme = get_theme()
        theme.background_color = pygame_menu.BaseImage(
            image_path,
            drawing_position=POSITION_CENTER,
        )
        native = prepare.NATIVE_RESOLUTION
        bg_size = theme.background_color.get_size()
        if bg_size[0] != native[0] or bg_size[1] != native[1]:
            raise ValueError(
                f"{image_path} {bg_size}: "
                f"It doesn't respect the native resolution {native}"
            )
        super().__init__(height=height, width=width)

        if image:
            new_image = pygame_menu.BaseImage(
                tools.transform_resource_filename(image),
                drawing_position=POSITION_CENTER,
            )
            image_size = new_image.get_size()
            if image_size[0] > native[0] or image_size[1] > native[1]:
                raise ValueError(
                    f"{image} {image_size}: "
                    f"It must be less than the native resolution {native}"
                )
            new_image.scale(prepare.SCALE, prepare.SCALE)
            self.menu.add.image(
                new_image,
                align=ALIGN_CENTER,
            )
