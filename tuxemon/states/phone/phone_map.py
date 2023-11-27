# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pygame_menu
from pygame_menu import locals
from pygame_menu.locals import POSITION_CENTER
from pygame_menu.widgets.selection.highlight import HighlightSelection

from tuxemon import prepare, tools
from tuxemon.locale import T
from tuxemon.menu.menu import BACKGROUND_COLOR, PygameMenuState
from tuxemon.menu.theme import get_theme
from tuxemon.session import local_session

MenuGameObj = Callable[[], Any]


def fix_measure(measure: int, percentage: float) -> int:
    """it returns the correct measure based on percentage"""
    return round(measure * percentage)


class NuPhoneMap(PygameMenuState):
    """
    This is experimental code for the NuPhone Map. Currently these map names are are hardcoded,
    but in the future, we will need to use some other data source to get the map names so that this
    code is not directly tied to any specific maps.
    """

    def add_menu_items(
        self,
        menu: pygame_menu.Menu,
    ) -> None:
        width, height = prepare.SCREEN_SIZE
        lab1 = menu.add.label(
            title=T.translate("leather_town"),
            selectable=True,
            float=True,
            selection_effect=HighlightSelection(),
            font_size=round(0.015 * width),
        )
        assert not isinstance(lab1, list)
        lab1.translate(
            fix_measure(menu._width, 0.20), fix_measure(menu._height, -0.03)
        )

        lab2 = menu.add.label(
            title=T.translate("cotton_town"),
            selectable=True,
            float=True,
            selection_effect=HighlightSelection(),
            font_size=round(0.015 * width),
        )
        assert not isinstance(lab2, list)
        lab2.translate(
            fix_measure(menu._width, 0.20), fix_measure(menu._height, 0.08)
        )

        lab3 = menu.add.label(
            title=T.translate("paper_town"),
            selectable=True,
            float=True,
            selection_effect=HighlightSelection(),
            font_size=round(0.015 * width),
        )
        assert not isinstance(lab3, list)
        lab3.translate(
            fix_measure(menu._width, 0.20), fix_measure(menu._height, 0.18)
        )

        lab4 = menu.add.label(
            title=T.translate("candy_town"),
            selectable=True,
            float=True,
            selection_effect=HighlightSelection(),
            font_size=round(0.015 * width),
        )
        assert not isinstance(lab4, list)
        lab4.translate(
            fix_measure(menu._width, -0.20), fix_measure(menu._height, 0.18)
        )

        lab5 = menu.add.label(
            title=T.translate("timber_town"),
            selectable=True,
            float=True,
            selection_effect=HighlightSelection(),
            font_size=round(0.015 * width),
        )
        assert not isinstance(lab5, list)
        lab5.translate(
            fix_measure(menu._width, -0.20), fix_measure(menu._height, -0.03)
        )

        lab6 = menu.add.label(
            title=T.translate("flower_city"),
            selectable=True,
            float=True,
            selection_effect=HighlightSelection(),
            font_size=round(0.015 * width),
        )
        assert not isinstance(lab6, list)
        lab6.translate(
            fix_measure(menu._width, -0.15), fix_measure(menu._height, -0.15)
        )
        # menu
        menu.set_title(title=T.translate("app_map")).center_content()

    def __init__(self) -> None:
        width, height = prepare.SCREEN_SIZE

        background = pygame_menu.BaseImage(
            image_path=tools.transform_resource_filename(
                "gfx/ui/item/new_spyder_map.png"
            ),
            drawing_position=POSITION_CENTER,
        )
        theme = get_theme()
        theme.scrollarea_position = locals.POSITION_EAST
        theme.background_color = background
        theme.widget_alignment = locals.ALIGN_CENTER

        # menu
        theme.title = True
        theme.title_font_size = round(0.025 * width)

        self.player = local_session.player

        super().__init__(
            height=height,
            width=width,
        )

        self.add_menu_items(self.menu)
        self.repristinate()

    def repristinate(self) -> None:
        """Repristinate original theme (color, alignment, etc.)"""
        theme = get_theme()
        theme.scrollarea_position = locals.SCROLLAREA_POSITION_NONE
        theme.background_color = BACKGROUND_COLOR
        theme.widget_alignment = locals.ALIGN_LEFT
        theme.title = False
