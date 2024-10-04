# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
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

        width, height = prepare.SCREEN_SIZE

        # define size window height
        if len(menu) >= 7:
            height = int(height * 0.8)
        else:
            height = int(height * (len(menu) / 7) * 0.8)

        # define size window width (longest word)
        name_item = max(len(element[0]) for element in menu)
        percentage_width = 0.4 if name_item > 10 else 0.3
        percentage_translate = 0.30 if name_item > 10 else 0.4
        width = int(width * percentage_width)

        super().__init__(width=width, height=height, **kwargs)

        for name, slug, callback in menu:
            try:
                item = db.lookup(slug, table="item")
            except KeyError:
                raise RuntimeError(f"Item {slug} not found")
            new_image = self._create_image(item.sprite)
            new_image.scale(prepare.SCALE * 0.5, prepare.SCALE * 0.5)
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
                fix_measure(width, percentage_translate),
                fix_measure(height, 0.05),
            )

        self.escape_key_exits = escape_key_exits
