# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from tuxemon.graphics import string_to_colorlike
from tuxemon.menu.menu import PygameMenuState
from tuxemon.menu.theme import get_theme

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient
    from tuxemon.platform.events import PlayerInput


class ColorState(PygameMenuState):
    """
    A state that overlays a solid color over the game world, allowing for
    dialogues, menus, or other UI elements to be displayed.
    """

    name: ClassVar[str] = "ColorState"

    def process_event(self, event: PlayerInput) -> PlayerInput | None:
        return None

    def __init__(self, client: BaseClient, color: str, **kwargs: Any) -> None:
        width, height = client.context.resolution
        _color = string_to_colorlike(color)

        super().__init__(client=client, height=height, width=width, **kwargs)

        theme = get_theme(self.client.context.scaling)

        if isinstance(_color, tuple) and len(_color) in (3, 4):
            theme.background_color = _color
        else:
            raise ValueError("Invalid color format for background_color")

        self._menu_config["theme"] = theme
        self.reset_theme()
