# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, Any, ClassVar

from pygame_menu.locals import ALIGN_CENTER, POSITION_EAST
from pygame_menu.menu import Menu

from tuxemon.locale.locale import T
from tuxemon.menu.menu import PygameMenuState
from tuxemon.platform.const.graphics import BG_PHONE_RENAMING
from tuxemon.platform.const.sizes import PLAYER_NAME_LIMIT

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient
    from tuxemon.entity.npc import NPC
    from tuxemon.monster.monster import Monster


class NuPhoneRenaming(PygameMenuState):
    name: ClassVar[str] = "NuPhoneRenaming"

    def add_menu_items(self, menu: Menu) -> None:
        def rename_callback(new_name: str, monster: Monster) -> None:
            monster.name = new_name
            self.menu.clear()
            theme = self._setup_theme(BG_PHONE_RENAMING)
            theme.scrollarea_position = POSITION_EAST
            theme.widget_alignment = ALIGN_CENTER
            self._menu_config["theme"] = theme
            self.add_menu_items(self.menu)

        def rename(monster: Monster) -> None:
            self.client.push_state(
                "InputMenu",
                prompt=T.translate("input_monster_name"),
                callback=partial(rename_callback, monster=monster),
                escape_key_exits=False,
                initial=monster.name,
                char_limit=PLAYER_NAME_LIMIT,
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

    def __init__(
        self, client: BaseClient, character: NPC, **kwargs: Any
    ) -> None:
        self.char = character
        width, height = client.context.resolution

        super().__init__(client=client, height=height, width=width, **kwargs)

        theme = self._setup_theme(BG_PHONE_RENAMING)
        theme.scrollarea_position = POSITION_EAST
        theme.widget_alignment = ALIGN_CENTER
        theme.title = True
        self._menu_config["theme"] = theme

        self.add_menu_items(self.menu)
        self.reset_theme()
