# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.locale import T
from tuxemon.menu.input import InputMenu
from tuxemon.menu.interface import MenuItem
from tuxemon.monster import Monster
from tuxemon.states.monster import MonsterMenuState
from tuxemon.states.world.worldstate import WorldState


@final
@dataclass
class RenameMonsterAction(EventAction):
    """
    Open the monster menu and text input screens to rename a selected monster.

    Script usage:
        .. code-block::

            rename_monster

    """

    name = "rename_monster"

    def start(self) -> None:
        # Get a copy of the world state.
        self.session.client.get_state_by_name(WorldState)

        # pull up the monster menu so we know which one we are renaming
        menu = self.session.client.push_state(MonsterMenuState())
        menu.on_menu_selection = self.prompt_for_name  # type: ignore[assignment]

    def update(self) -> None:

        missing_monster_menu = False

        try:
            self.session.client.get_state_by_name(MonsterMenuState)
        except ValueError:
            missing_monster_menu = True

        try:
            self.session.client.get_state_by_name(InputMenu)
        except ValueError:
            if missing_monster_menu:
                self.stop()

    def set_monster_name(self, name: str) -> None:
        self.monster.name = name
        monster_menu_state = self.session.client.get_state_by_name(
            MonsterMenuState,
        )
        monster_menu_state.refresh_menu_items()

    def prompt_for_name(self, menu_item: MenuItem[Monster]) -> None:
        self.monster = menu_item.game_object

        self.session.client.push_state(
            InputMenu(
                prompt=T.translate("input_monster_name"),
                callback=self.set_monster_name,
                escape_key_exits=False,
                initial=T.translate(self.monster.slug),
            )
        )
