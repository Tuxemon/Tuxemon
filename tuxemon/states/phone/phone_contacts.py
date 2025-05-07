# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Callable
from functools import partial
from typing import TYPE_CHECKING, Any

import pygame_menu
from pygame_menu import locals
from pygame_menu.widgets.selection.highlight import HighlightSelection

from tuxemon import prepare
from tuxemon.locale import T
from tuxemon.menu.menu import PygameMenuState
from tuxemon.relationship import RELATIONSHIP_STRENGTH
from tuxemon.session import local_session
from tuxemon.tools import open_choice_dialog, open_dialog

if TYPE_CHECKING:
    from tuxemon.npc import NPC

MenuGameObj = Callable[[], Any]


def fix_measure(measure: int, percentage: float) -> int:
    """it returns the correct measure based on percentage"""
    return round(measure * percentage)


class NuPhoneContacts(PygameMenuState):
    def add_menu_items(
        self,
        menu: pygame_menu.Menu,
    ) -> None:
        def choice(slug: str) -> None:
            label = f"{T.translate('action_call')} {T.translate(slug).upper()}"
            var_menu = []
            var_menu.append((label, label, call))
            open_choice_dialog(
                local_session,
                menu=(var_menu),
                escape_key_exits=True,
            )

        def call() -> None:
            self.client.pop_state()
            self.client.pop_state()
            # from spyder_cotton_town.tmx to spyder_cotton_town
            map = self.client.get_map_name()
            map_name = map.split(".")[0]
            if T.translate(map_name) != map_name:
                open_dialog(
                    local_session,
                    [T.translate(map_name)],
                )
            else:
                open_dialog(
                    local_session,
                    [T.translate("phone_no_answer")],
                )

        # slug and phone number from the tuple
        connections = self.char.relationships.get_all_connections()
        for slug, contact in connections.items():
            menu.add.button(
                title=T.translate(slug),
                action=partial(choice, slug),
                font_size=self.font_size_small,
                selection_effect=HighlightSelection(),
            )
            relationship = T.translate(f"relation_relationship")
            relation = T.translate(f"relation_{contact.relationship_type}")
            menu.add.label(
                title=f"{relationship}: {relation}",
                font_size=self.font_size_small,
            )
            relation_strength = T.translate(f"relation_strength")
            menu.add.label(
                title=f"{relation_strength}: {contact.strength}/{RELATIONSHIP_STRENGTH[1]}",
                font_size=self.font_size_small,
            )
            menu.add.vertical_margin(25)

        # menu
        menu.set_title(T.translate("app_contacts")).center_content()

    def __init__(self, character: NPC) -> None:
        width, height = prepare.SCREEN_SIZE

        theme = self._setup_theme(prepare.BG_PHONE_CONTACTS)
        theme.scrollarea_position = locals.POSITION_EAST
        theme.widget_alignment = locals.ALIGN_CENTER

        # menu
        theme.title = True

        self.char = character

        super().__init__(
            height=height,
            width=width,
        )

        for relation in self.char.relationships.connections.values():
            relation.apply_decay(self.char)

        self.add_menu_items(self.menu)
        self.reset_theme()
