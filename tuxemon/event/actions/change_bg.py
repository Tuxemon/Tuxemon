# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, final

from pygame_menu import locals

from tuxemon import prepare
from tuxemon.db import db
from tuxemon.event.eventaction import EventAction
from tuxemon.menu.theme import get_theme
from tuxemon.states.idle.color_state import ColorState
from tuxemon.states.idle.image_state import ImageState

logger = logging.getLogger()

CATEGORIES: list[str] = ["image", "monster", "template", "item"]
CATEGORY_PATHS: dict[str, str] = {
    "monster": "gfx/sprites/battle/{}-front.png",
    "template": "gfx/sprites/player/{}.png",
    "item": "gfx/items/{}.png",
    "image": "gfx/ui/background/{}.png",
}


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

            change_bg <background>[,image][,category]

    Script parameters:
        background:
        - it can be the name of the file (see below note)
        - it can be a RGB color separated by ":" (eg 255:0:0)

        image: monster_slug or template_slug or path
            if path, then "gfx/ui/background/"
            if template (eg. ceo) in "gfx/sprites/player"
            "change_bg gradient_blue,ceo"

        category: (optional) category of the image (e.g. monster, template, etc.)
            if not provided, it will default to "background"

        note: the background or image (if not monster or template)
            must be inside the folder (gfx/ui/background/)

        background size: 240x160

    """

    name = "change_bg"
    background: Optional[str] = None
    image: Optional[str] = None
    category: Optional[str] = None

    def start(self) -> None:
        # don't override previous state if we are still in the state.
        client = self.session.client
        if client.current_state is None:
            # obligatory "should not happen"
            raise RuntimeError

        # this function cleans up the previous state without crashing
        if len(client.state_manager.active_states) > 2:
            client.pop_state()

        if self.image and self.category:
            if self.category not in CATEGORIES:
                logger.error(f"{self.category} must be among {CATEGORIES}")
                return
            if self.category == "image":
                self.image = CATEGORY_PATHS[self.category].format(self.image)
            elif self.image in db.database["monster"]:
                self.image = CATEGORY_PATHS[self.category].format(self.image)
            elif self.image in db.database["template"]:
                self.image = CATEGORY_PATHS[self.category].format(self.image)
            elif self.image in db.database["item"]:
                self.image = CATEGORY_PATHS[self.category].format(self.image)
            else:
                logger.error(
                    f"Image {self.image} not found in category {self.category}"
                )
                return

        if client.current_state.name != str(ImageState):
            if self.background is None:
                if len(client.state_manager.active_states) > 2:
                    client.pop_state()
                    return
            else:
                _background = self.background.split(":")
                if len(_background) == 1:
                    client.push_state(
                        ImageState(
                            background=self.background, image=self.image
                        )
                    )
                else:
                    client.push_state(ColorState(color=self.background))

    def cleanup(self) -> None:
        theme = get_theme()
        theme.background_color = prepare.BACKGROUND_COLOR
        theme.widget_alignment = locals.ALIGN_LEFT
