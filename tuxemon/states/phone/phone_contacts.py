# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Callable
from functools import partial
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
from tuxemon.tools import open_choice_dialog, open_dialog

MenuGameObj = Callable[[], Any]


def fix_measure(measure: int, percentage: float) -> int:
    """it returns the correct measure based on percentage"""
    return round(measure * percentage)


class NuPhoneContacts(PygameMenuState):
    def add_menu_items(
        self,
        menu: pygame_menu.Menu,
    ) -> None:
        def choice(slug: str, phone: str) -> None:
            label = (
                T.translate("action_call") + " " + T.translate(slug).upper()
            )
            var_menu = []
            var_menu.append((label, label, partial(call, phone)))
            open_choice_dialog(
                local_session,
                menu=(var_menu),
                escape_key_exits=True,
            )

        def call(phone: str) -> None:
            self.client.pop_state()
            self.client.pop_state()
            # from spyder_cotton_town.tmx to spyder_cotton_town
            map = self.client.get_map_name()
            map_name = map.split(".")[0]
            # new string map + phone
            new_label = f"{map_name}_{phone}"
            if T.translate(new_label) != new_label:
                open_dialog(
                    local_session,
                    [T.translate(new_label)],
                )
            else:
                open_dialog(
                    local_session,
                    [T.translate("phone_no_answer")],
                )

        # slug and phone number from the tuple
        for slug, phone in self.player.contacts.items():
            menu.add.button(
                title=T.translate(slug) + " " + phone,
                action=partial(choice, slug, phone),
                button_id=slug,
                font_size=self.font_size_small,
                selection_effect=HighlightSelection(),
            )
            menu.add.vertical_margin(25)

        # menu
        menu.set_title(T.translate("app_contacts")).center_content()

    def __init__(self) -> None:
        width, height = prepare.SCREEN_SIZE

        background = pygame_menu.BaseImage(
            image_path=tools.transform_resource_filename(
                prepare.BG_PHONE_CONTACTS
            ),
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
