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
from tuxemon.menu.menu import PygameMenuState
from tuxemon.menu.theme import get_theme
from tuxemon.session import local_session

MenuGameObj = Callable[[], Any]


def fix_measure(measure: int, percentage: float) -> int:
    """it returns the correct measure based on percentage"""
    return round(measure * percentage)


class NuPhoneMap(PygameMenuState):
    """
    The map will be generated from a game variable called: "phone_map"
    If there is no variable, then it'll be shown the Spyder map.

    The coordinates of the cities / location will be obtained by game variables
    beginning with the prefix: "nu_map_"
    where location is the msgid of the location (PO), x and y are coordinates

    If the player is in Cotton Town, then Cotton Town will be underlined and not
    selectable.

    If there are no trackers (locations), then it'll be not possible to consult
    the app. It'll appear a pop up with: "GPS tracker not updating."

    Some examples:
    game_variables["nu_map_1"] = "leather_town*0.20*0.42"
    game_variables["nu_map_2"] = "cotton_town*0.20*0.52"
    game_variables["nu_map_3"] = "paper_town*0.20*0.62"
    game_variables["nu_map_4"] = "candy_town*-0.15*0.62"
    game_variables["nu_map_5"] = "timber_town*-0.15*0.42"
    game_variables["nu_map_6"] = "flower_city*-0.15*0.32"

    """

    def add_menu_items(
        self,
        menu: pygame_menu.Menu,
    ) -> None:
        phone_map = self.player.game_variables.get(
            "phone_map", prepare.PHONE_MAP
        )
        # map
        new_image = pygame_menu.BaseImage(
            tools.transform_resource_filename(phone_map)
        )
        new_image.scale(prepare.SCALE, prepare.SCALE)
        menu.add.image(image_path=new_image.copy())
        underline = False
        selectable = True

        for key, value in self.player.game_variables.items():
            if key.startswith("nu_map_"):
                info = value.split("*")
                place = info[0]
                x = float(info[1])
                y = float(info[2])
                # player is here
                if self.client.map_slug == place:
                    underline = True
                    selectable = False

                place = menu.add.label(
                    title=T.translate(place),
                    selectable=selectable,
                    float=True,
                    underline=underline,
                    font_size=self.font_size_small,
                )
                assert not isinstance(place, list)
                place.translate(
                    fix_measure(menu._width, x), fix_measure(menu._height, y)
                )

        # menu
        menu.set_title(title=T.translate("app_map")).center_content()

    def __init__(self) -> None:
        width, height = prepare.SCREEN_SIZE

        background = pygame_menu.BaseImage(
            image_path=tools.transform_resource_filename(prepare.BG_PHONE_MAP),
            drawing_position=POSITION_CENTER,
        )
        theme = get_theme()
        theme.scrollarea_position = locals.POSITION_EAST
        theme.background_color = background
        theme.widget_alignment = locals.ALIGN_CENTER

        # menu
        theme.title = True

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
        theme.background_color = self.background_color
        theme.widget_alignment = locals.ALIGN_LEFT
        theme.title = False
