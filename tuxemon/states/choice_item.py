# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, ClassVar

from pygame_menu.locals import POSITION_EAST
from pygame_menu.widgets.selection.highlight import HighlightSelection

from tuxemon.database.runtime import db
from tuxemon.db import ItemModel
from tuxemon.menu.menu import PygameMenuState
from tuxemon.menu.theme import get_theme
from tuxemon.tools import fix_measure
from tuxemon.ui.menu_options import MenuOptions

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient


@dataclass
class MenuItemConfig:
    max_elements: int = 7
    max_height_percentage: float = 0.8
    length_name_item: int = 10
    scale_sprite: float = 0.5
    window_width_percentage_long: float = 0.4
    window_width_percentage_short: float = 0.3
    translate_percentage_long: float = 0.4
    translate_percentage_short: float = 0.3
    translate_percentage_vertical_offset: float = 0.05


class ChoiceItem(PygameMenuState):
    """
    Game state with a graphic box and items (images) + labels.
    """

    name: ClassVar[str] = "ChoiceItem"

    def __init__(
        self,
        client: BaseClient,
        menu: MenuOptions,
        escape_key_exits: bool = False,
        config: MenuItemConfig | None = None,
        **kwargs: Any,
    ) -> None:
        self.config = config or MenuItemConfig()

        self.width, self.height, self.translate_percentage = (
            self.calculate_window_size(menu)
        )
        super().__init__(
            client=client, width=self.width, height=self.height, **kwargs
        )
        theme = get_theme(self.client.context.scaling).copy()
        theme.scrollarea_position = POSITION_EAST
        self._menu_config["theme"] = theme

        for option in menu.get_menu():
            self.add_item_menu_item(
                option.display_text, option.key, option.action
            )

        self.escape_key_exits = escape_key_exits

    def calculate_window_size(
        self, menu: MenuOptions
    ) -> tuple[int, int, float]:
        _width, _height = self.client.context.resolution

        if len(menu.options) >= self.config.max_elements:
            height = _height * self.config.max_height_percentage
        else:
            height = (
                _height
                * (len(menu.options) / self.config.max_elements)
                * self.config.max_height_percentage
            )

        name_item = max(len(element.key) for element in menu.options)
        if name_item > self.config.length_name_item:
            width = _width * self.config.window_width_percentage_long
            translate_percentage = self.config.translate_percentage_short
        else:
            width = _width * self.config.window_width_percentage_short
            translate_percentage = self.config.translate_percentage_long

        return int(width), int(height), translate_percentage

    def add_item_menu_item(
        self,
        name: str,
        slug: str,
        callback: Callable[[], None],
    ) -> None:
        item = ItemModel.lookup(slug, db)
        new_image = self._create_image(item.sprite)
        scaled = self.factor * self.config.scale_sprite
        new_image.scale(scaled, scaled)
        self.menu.add.image(new_image)
        self.menu.add.button(
            name,
            callback,
            font_size=self.font_type.smaller,
            float=True,
            selection_effect=HighlightSelection(),
        ).translate(
            fix_measure(self.width, self.translate_percentage),
            fix_measure(
                self.height, self.config.translate_percentage_vertical_offset
            ),
        )
