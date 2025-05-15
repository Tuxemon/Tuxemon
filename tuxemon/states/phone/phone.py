# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from functools import partial
from typing import TYPE_CHECKING, Any

import pygame_menu
from pygame_menu import locals
from pygame_menu.widgets.selection.highlight import HighlightSelection

from tuxemon import prepare
from tuxemon.item.item import Item
from tuxemon.locale import T
from tuxemon.map_manager import MAP_TYPES
from tuxemon.menu.menu import PygameMenuState
from tuxemon.tools import open_dialog

if TYPE_CHECKING:
    from tuxemon.npc import NPC

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
        self._no_signal = False

        def _change_state(state: str, **kwargs: Any) -> MenuGameObj:
            return partial(self.client.push_state, state, **kwargs)

        def _no_trackers() -> None:
            no_trackers = T.translate("nu_map_missing")
            open_dialog(self.client, [no_trackers])

        def _no_signal() -> None:
            no_signal = T.translate("no_signal")
            open_dialog(self.client, [no_signal])

        def _uninstall(itm: Item) -> None:
            count = sum([1 for ele in self.char.items if ele.slug == itm.slug])
            if count > 1:
                self.char.remove_item(itm)
                self.client.replace_state("NuPhone", character=self.char)
            else:
                open_dialog(
                    self.client,
                    [T.translate("uninstall_app")],
                )

        menu._column_max_width = [
            fix_measure(menu._width, 0.25),
            fix_measure(menu._width, 0.25),
            fix_measure(menu._width, 0.25),
            fix_measure(menu._width, 0.25),
        ]

        # menu
        network = [
            mt for mt in MAP_TYPES if mt.name in {"town", "clinic", "shop"}
        ]
        desc = T.translate("nu_phone")
        if self.client.map_manager.map_type in network:
            desc = T.translate("omnichannel_mobile")
        else:
            desc = T.translate("no_signal")
            self._no_signal = True
        menu.set_title(desc).center_content()

        # no gps tracker (nu map)
        trackers = self.char.tracker.locations

        for item in items:
            label = T.translate(item.name).upper()
            change = None
            if item.slug == "app_banking":
                change = (
                    _no_signal
                    if self._no_signal
                    else _change_state("NuPhoneBanking", character=self.char)
                )
            elif item.slug == "app_contacts":
                change = _change_state("NuPhoneContacts", character=self.char)
            elif item.slug == "app_map":
                change = (
                    _change_state("NuPhoneMap", character=self.char)
                    if trackers
                    else _no_trackers
                )
            new_image = self._create_image(item.sprite)
            new_image.scale(prepare.SCALE, prepare.SCALE)
            # image of the app
            menu.add.banner(
                new_image,
                change,
                selection_effect=HighlightSelection(),
            )
            # name of the app
            menu.add.button(
                label,
                action=partial(_uninstall, item),
                font_size=self.font_size_smaller,
            )
            # description of the app
            menu.add.label(
                item.description,
                font_size=self.font_size_smaller,
                wordwrap=True,
            )

    def __init__(self, character: NPC) -> None:
        width, height = prepare.SCREEN_SIZE

        theme = self._setup_theme(prepare.BG_PHONE)
        theme.scrollarea_position = locals.POSITION_EAST
        theme.widget_alignment = locals.ALIGN_CENTER

        # menu
        theme.title = True

        self.char = character

        menu_items_map = []
        for itm in self.char.items:
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
        self.reset_theme()
