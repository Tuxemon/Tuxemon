# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from pygame_menu.locals import ALIGN_CENTER

from tuxemon.menu.menu import PygameMenuState
from tuxemon.platform.const.sizes import NATIVE_RESOLUTION

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient
    from tuxemon.platform.events import PlayerInput


class ImageState(PygameMenuState):
    """
    A state that overlays an image over the game world, useful for displaying
    dialogues, menus, or other UI elements.
    """

    name: ClassVar[str] = "ImageState"

    def process_event(self, event: PlayerInput) -> PlayerInput | None:
        return None

    def __init__(
        self,
        client: BaseClient,
        background: str,
        image: str | None = None,
        **kwargs: Any,
    ) -> None:
        width, height = client.context.resolution
        image_path = f"gfx/ui/background/{background}.png"
        native = NATIVE_RESOLUTION

        super().__init__(client=client, height=height, width=width, **kwargs)

        theme = self._setup_theme(image_path)
        self._menu_config["theme"] = theme

        bg_size = self._create_image(image_path).get_size()
        if bg_size[0] != native[0] or bg_size[1] != native[1]:
            raise ValueError(
                f"{image_path} {bg_size}: "
                f"It doesn't respect the native resolution {native}"
            )

        if image:
            new_image = self._create_image(image)
            image_size = new_image.get_size()
            if image_size[0] > native[0] or image_size[1] > native[1]:
                raise ValueError(
                    f"{image} {image_size}: "
                    f"It must be less than the native resolution {native}"
                )
            new_image.scale(self.factor, self.factor)
            self.menu.add.image(
                new_image,
                align=ALIGN_CENTER,
            )
        self.reset_theme()
