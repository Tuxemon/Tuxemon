# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from functools import partial
from typing import Any

import pygame_menu
from pygame_menu import locals
from pygame_menu.locals import POSITION_CENTER
from pygame_menu.widgets.selection.highlight import HighlightSelection

from tuxemon import prepare, tools
from tuxemon.item.item import Item
from tuxemon.locale import T
from tuxemon.menu.menu import BACKGROUND_COLOR, PygameMenuState
from tuxemon.menu.theme import get_theme
from tuxemon.session import local_session
from tuxemon.tools import open_dialog

MenuGameObj = Callable[[], Any]


def fix_measure(measure: int, percentage: float) -> int:
    """it returns the correct measure based on percentage"""
    return round(measure * percentage)


class NuPhone(PygameMenuState):
    """Menu for Nu Phone."""

    def add_menu_items(
        self,
        menu: pygame_menu.Menu,
        items: Sequence[Item],
    ) -> None:
        width, height = prepare.SCREEN_SIZE
        self._no_signal = False

        def change_state(state: str, **kwargs: Any) -> MenuGameObj:
            return partial(self.client.push_state, state, **kwargs)

        def no_signal() -> None:
            open_dialog(
                local_session,
                [T.translate("no_signal")],
            )

        def uninstall(itm: Item) -> None:
            count = sum(
                [1 for ele in self.player.items if ele.slug == itm.slug]
            )
            if count > 1:
                self.player.remove_item(itm)
                self.client.replace_state("NuPhone")
            else:
                open_dialog(
                    local_session,
                    [T.translate("uninstall_app")],
                )

        menu._column_max_width = [
            fix_measure(menu._width, 0.25),
            fix_measure(menu._width, 0.25),
            fix_measure(menu._width, 0.25),
            fix_measure(menu._width, 0.25),
        ]

        # menu
        network = ["town", "clinic", "shop"]
        desc = T.translate("nu_phone")
        if local_session.client.map_type in network:
            desc = T.translate("omnichannel_mobile")
        else:
            desc = T.translate("no_signal")
            self._no_signal = True
        menu.set_title(desc).center_content()

        for item in items:
            label = T.translate(item.name).upper()
            change = None
            if item.slug == "app_banking":
                if self._no_signal is True:
                    change = no_signal
                else:
                    change = change_state("NuPhoneBanking")
            elif item.slug == "app_contacts":
                change = change_state("NuPhoneContacts")
            elif item.slug == "app_map":
                change = change_state("NuPhoneMap")
            new_image = pygame_menu.BaseImage(
                tools.transform_resource_filename(item.sprite),
                drawing_position=POSITION_CENTER,
            )
            new_image.scale(prepare.SCALE, prepare.SCALE)
            menu.add.banner(
                new_image,
                change,
                selection_effect=HighlightSelection(),
            )
            menu.add.button(
                label,
                action=partial(uninstall, item),
                font_size=round(0.012 * width),
            )
            menu.add.label(
                item.description, font_size=round(0.012 * width), wordwrap=True
            )

    def __init__(self) -> None:
        width, height = prepare.SCREEN_SIZE

        background = pygame_menu.BaseImage(
            image_path=tools.transform_resource_filename(
                "gfx/ui/item/bg_pcstate.png"
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

        menu_items_map = []
        for itm in self.player.items:
            if (
                itm.category == "phone"
                and itm.slug != "nu_phone"
                and itm.slug != "app_tuxepedia"
            ):
                menu_items_map.append(itm)

        # 4 columns, then 3 rows (image + label + description)
        columns = 4
        rows = math.ceil(len(menu_items_map) / columns) * 3

        super().__init__(
            height=height, width=width, columns=columns, rows=rows
        )

        self.add_menu_items(self.menu, menu_items_map)
        self.repristinate()

    def repristinate(self) -> None:
        """Repristinate original theme (color, alignment, etc.)"""
        theme = get_theme()
        theme.scrollarea_position = locals.SCROLLAREA_POSITION_NONE
        theme.background_color = BACKGROUND_COLOR
        theme.widget_alignment = locals.ALIGN_LEFT
        theme.title = False
