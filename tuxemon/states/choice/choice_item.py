# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from pygame_menu.locals import POSITION_EAST
from pygame_menu.widgets.selection.highlight import HighlightSelection

from tuxemon import prepare
from tuxemon.db import db
from tuxemon.menu.menu import PygameMenuState
from tuxemon.menu.theme import get_theme

ChoiceMenuGameObj = Callable[[], None]
LENGTH_NAME_ITEM = 10
MAX_MENU_ELEMENTS = 7
MAX_MENU_HEIGHT_PERCENTAGE = 0.8
SCALE_SPRITE = 0.5
WINDOW_WIDTH_PERCENTAGE_LONG = 0.4
WINDOW_WIDTH_PERCENTAGE_SHORT = 0.3
TRANSLATE_PERCENTAGE_LONG = 0.4
TRANSLATE_PERCENTAGE_SHORT = 0.3


def fix_measure(measure: int, percentage: float) -> int:
    """it returns the correct measure based on percentage"""
    return round(measure * percentage)


class ChoiceItem(PygameMenuState):
    """
    Game state with a graphic box and items (images) + labels.

    """

    def __init__(
        self,
        menu: Sequence[tuple[str, str, Callable[[], None]]] = (),
        escape_key_exits: bool = False,
        **kwargs: Any,
    ) -> None:
        theme = get_theme()
        theme.scrollarea_position = POSITION_EAST

        self.width, self.height, self.translate_percentage = (
            self.calculate_window_size(menu)
        )
        super().__init__(width=self.width, height=self.height, **kwargs)

        for name, slug, callback in menu:
            self.add_item_menu_item(name, slug, callback)

        self.escape_key_exits = escape_key_exits

    def calculate_window_size(
        self, menu: Sequence[tuple[str, str, Callable[[], None]]]
    ) -> tuple[int, int, float]:
        _width, _height = prepare.SCREEN_SIZE

        if len(menu) >= MAX_MENU_ELEMENTS:
            height = _height * MAX_MENU_HEIGHT_PERCENTAGE
        else:
            height = (
                _height
                * (len(menu) / MAX_MENU_ELEMENTS)
                * MAX_MENU_HEIGHT_PERCENTAGE
            )

        name_item = max(len(element[0]) for element in menu)
        if name_item > LENGTH_NAME_ITEM:
            width = _width * WINDOW_WIDTH_PERCENTAGE_LONG
            translate_percentage = TRANSLATE_PERCENTAGE_SHORT
        else:
            width = _width * WINDOW_WIDTH_PERCENTAGE_SHORT
            translate_percentage = TRANSLATE_PERCENTAGE_LONG

        return int(width), int(height), translate_percentage

    def add_item_menu_item(
        self,
        name: str,
        slug: str,
        callback: Callable[[], None],
    ) -> None:
        try:
            item = db.lookup(slug, table="item")
        except KeyError:
            raise RuntimeError(f"Item {slug} not found")
        new_image = self._create_image(item.sprite)
        new_image.scale(
            prepare.SCALE * SCALE_SPRITE, prepare.SCALE * SCALE_SPRITE
        )
        self.menu.add.image(
            new_image,
        )
        self.menu.add.button(
            name,
            callback,
            font_size=self.font_size_smaller,
            float=True,
            selection_effect=HighlightSelection(),
        ).translate(
            fix_measure(self.width, self.translate_percentage),
            fix_measure(self.height, 0.05),
        )
