# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, ClassVar

from pygame_menu.locals import ALIGN_CENTER, POSITION_EAST
from pygame_menu.widgets.selection.highlight import HighlightSelection

from tuxemon.database.runtime import db
from tuxemon.db import NpcModel
from tuxemon.entity.sheet import get_combat_sheet
from tuxemon.graphics import scale_surface
from tuxemon.menu.menu import PygameMenuState
from tuxemon.menu.theme import get_theme
from tuxemon.menu.transitions import PopInClamped
from tuxemon.ui.menu_options import MenuOptions

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient


@dataclass
class MenuNpcConfig:
    max_elements: int = 12
    max_height_percentage: float = 0.8
    number_widgets: int = 3
    number_columns: int = 4
    scale_sprite: float = 0.4
    vertical_fill: int = 10


class ChoiceNpc(PygameMenuState):
    """
    Game state with a graphic box and NPCs (images) + labels.
    """

    name: ClassVar[str] = "ChoiceNpc"

    def __init__(
        self,
        client: BaseClient,
        menu: MenuOptions,
        escape_key_exits: bool = False,
        config: MenuNpcConfig | None = None,
        **kwargs: Any,
    ) -> None:
        self.config = config or MenuNpcConfig()

        rows = (
            math.ceil(len(menu.options) / self.config.number_columns)
            * self.config.number_widgets
        )

        super().__init__(
            client=client,
            columns=self.config.number_columns,
            rows=rows,
            transition=PopInClamped(
                max_height_percentage=self.config.max_height_percentage
            ),
            **kwargs,
        )

        theme = get_theme(self.client.context.scaling).copy()

        if len(menu.options) > self.config.max_elements:
            theme.scrollarea_position = POSITION_EAST

        self._menu_config["theme"] = theme

        for option in menu.get_menu():
            self.add_npc_menu_item(
                option.display_text, option.key, option.action
            )

        self.escape_key_exits = escape_key_exits

    def add_npc_menu_item(
        self,
        name: str,
        slug: str,
        callback: Callable[[], None],
    ) -> None:
        npc = NpcModel.lookup(slug, db)
        sheet = get_combat_sheet(npc.template)
        surface = sheet.front()
        scaled = scale_surface(surface, self.factor * self.config.scale_sprite)
        new_image = self._create_image_from_surface(scaled)
        self.menu.add.image(new_image, align=ALIGN_CENTER)
        # replace slug not translated
        if name == slug:
            name = "???"
        self.menu.add.button(
            name,
            callback,
            font_size=self.font_type.smaller,
            align=ALIGN_CENTER,
            selection_effect=HighlightSelection(),
        )
        self.menu.add.vertical_fill(self.config.vertical_fill)
