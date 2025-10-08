# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, ClassVar

import pygame_menu
from pygame_menu import locals

from tuxemon import prepare
from tuxemon.locale import T
from tuxemon.menu.menu import PygameMenuState

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.npc import NPC


class NuPhoneRenaming(PygameMenuState):
    name: ClassVar[str] = "NuPhoneRenaming"

    def add_menu_items(
        self,
        menu: pygame_menu.Menu,
    ) -> None:
        def rename_callback(new_name: str, monster: Monster) -> None:
            monster.name = new_name
            self.menu.clear()
            theme = self._setup_theme(prepare.BG_PHONE_RENAMING)
            theme.scrollarea_position = locals.POSITION_EAST
            theme.widget_alignment = locals.ALIGN_CENTER
            self.add_menu_items(self.menu)

        def rename(monster: Monster) -> None:
            self.client.push_state(
                "InputMenu",
                prompt=T.translate("input_monster_name"),
                callback=partial(rename_callback, monster=monster),
                escape_key_exits=False,
                initial=monster.name,
                char_limit=prepare.PLAYER_NAME_LIMIT,
            )

        monsters = self.char.party.monsters
        for monster in monsters:
            renaming = T.translate("renaming")
            menu.add.button(
                title=f"{renaming}: {monster.name}",
                action=partial(rename, monster),
                font_size=self.font_type.medium,
            )
            menu.add.vertical_margin(25)

        menu.set_title(T.translate("app_renaming")).center_content()

    def __init__(self, character: NPC) -> None:
        width, height = prepare.SCREEN_SIZE

        theme = self._setup_theme(prepare.BG_PHONE_RENAMING)
        theme.scrollarea_position = locals.POSITION_EAST
        theme.widget_alignment = locals.ALIGN_CENTER
        theme.title = True

        self.char = character

        super().__init__(
            height=height,
            width=width,
        )

        self.add_menu_items(self.menu)
        self.reset_theme()
