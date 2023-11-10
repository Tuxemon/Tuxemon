# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

import pygame_menu
from pygame_menu.locals import POSITION_CENTER, POSITION_EAST
from pygame_menu.widgets.selection.highlight import HighlightSelection

from tuxemon import prepare
from tuxemon.db import db
from tuxemon.menu.menu import PygameMenuState
from tuxemon.menu.theme import get_theme
from tuxemon.tools import transform_resource_filename

ChoiceMenuGameObj = Callable[[], None]


def fix_width(screen_x: int, pos_x: float) -> int:
    """it returns the correct width based on percentage"""
    value = round(screen_x * pos_x)
    return value


def fix_height(screen_y: int, pos_y: float) -> int:
    """it returns the correct height based on percentage"""
    value = round(screen_y * pos_y)
    return value


class ChoiceItem(PygameMenuState):
    """
    Game state with a graphic box and some text in it.

    Pressing the action button:
    * if text is being displayed, will cause text speed to go max
    * when text is displayed completely, then will show the next message
    * if there are no more messages, then the dialog will close
    """

    def __init__(
        self,
        menu: Sequence[tuple[str, str, Callable[[], None]]] = (),
        escape_key_exits: bool = False,
        **kwargs: Any,
    ) -> None:
        theme = get_theme()
        theme.scrollarea_position = POSITION_EAST
        theme.scrollbar_color = (237, 246, 248)
        theme.scrollbar_slider_color = (197, 232, 234)

        width, height = prepare.SCREEN_SIZE
        width = int(width * 0.4)
        if len(menu) >= 7:
            height = int(height * 0.8)
        else:
            height = int(height * (len(menu) / 7) * 0.8)

        super().__init__(width=width, height=height, **kwargs)

        for _key, label, callback in menu:
            item = db.lookup(label, table="item")
            new_image = pygame_menu.BaseImage(
                transform_resource_filename(item.sprite),
                drawing_position=POSITION_CENTER,
            )
            new_image.scale(prepare.SCALE * 0.5, prepare.SCALE * 0.5)
            self.menu.add.image(
                new_image,
            )
            self.menu.add.button(
                _key,
                callback,
                font_size=15,
                float=True,
                selection_effect=HighlightSelection(),
            ).translate(fix_width(width, 0.25), fix_height(height, 0.05))

        self.escape_key_exits = escape_key_exits
