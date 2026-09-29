# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.database.runtime import db
from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session

logger = logging.getLogger()

CATEGORIES: list[str] = ["image", "item"]
CATEGORY_PATHS: dict[str, str] = {
    "item": "gfx/items/{}.png",
    "image": "gfx/ui/background/{}.png",
}


@final
@dataclass
class ChangeBgAction(EventAction):
    """
    Handles the background change within the session, allowing users
    to apply a new background color or image dynamically.

    Script usage:
        .. code-block::

            change_bg <background>[,image][,category]

    Script parameters:
        background: The background identifier, which can be:
            - A file name located in `gfx/ui/background/`
            - An RGB color formatted as `R:G:B` (e.g., `255:0:0`)
        image: An optional image identifier, which can be:
            - An item slug (stored in `gfx/items`)
            - A direct file path
        category: The category of the image (e.g., item or image.
            If omitted, defaults to "background".

    Notes:
        - Background images must be in `gfx/ui/background/`.
        - Background dimensions must be 256x144 pixels.
    """

    name = "change_bg"
    background: str | None = None
    image: str | None = None
    category: str | None = None

    def start(self, session: Session) -> None:

        client = session.client
        if client.current_state is None:
            raise RuntimeError

        if client.has_extra_states():
            client.pop_state()

        if self.image and self.category:
            if self.category not in CATEGORIES:
                logger.error(f"{self.category} must be among {CATEGORIES}")
                self.stop()
                return
            if self.category == "image":
                self.image = CATEGORY_PATHS[self.category].format(self.image)
            elif self.image in db.database["item"]:
                self.image = CATEGORY_PATHS[self.category].format(self.image)
            else:
                logger.error(
                    f"Image {self.image} not found in category {self.category}"
                )
                self.stop()
                return

        if client.current_state.name != "ImageState":
            if self.background is None:
                if client.has_extra_states():
                    client.pop_state()
                    self.stop()
                    return
            else:
                _background = self.background.split(":")
                if len(_background) == 1:
                    client.push_state(
                        "ImageState",
                        background=self.background,
                        image=self.image,
                    )

                else:
                    client.push_state("ColorState", color=self.background)
