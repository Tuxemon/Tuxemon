# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Callable
from functools import partial
from typing import TYPE_CHECKING, Any, Optional

import pygame_menu

from tuxemon import prepare
from tuxemon.animation import Animation, ScheduleType
from tuxemon.locale import T
from tuxemon.menu.menu import PygameMenuState
from tuxemon.state.state import State
from tuxemon.tools import open_dialog

if TYPE_CHECKING:
    from tuxemon.client import LocalPygameClient
    from tuxemon.npc import NPC

MenuGameObj = Callable[[], object]


def add_menu_items(
    menu: pygame_menu.Menu,
    items: list[tuple[str, MenuGameObj]],
) -> None:
    for key, callback in items:
        label = T.translate(key).upper()
        menu.add.button(label, callback)


class MenuProvider:
    def get_menu_items(
        self, client: LocalPygameClient, character: NPC
    ) -> list[tuple[str, MenuGameObj]]:
        raise NotImplementedError


class PCMenuBuilder:
    """Builds the menu items for the PCState."""

    def __init__(
        self,
        client: LocalPygameClient,
        character: NPC,
        menu_providers: Optional[list[MenuProvider]] = None,
    ) -> None:
        self.client = client
        self.character = character
        self.menu_providers = (
            menu_providers if menu_providers is not None else []
        )

    def _change_state(self, state: str, **kwargs: Any) -> partial[State]:
        return partial(self.client.replace_state, state, **kwargs)

    def _not_implemented_dialog(self) -> None:
        open_dialog(self.client, [T.translate("not_implemented")])

    def build_menu_items(self) -> list[tuple[str, MenuGameObj]]:
        char = self.character
        menu: list[tuple[str, MenuGameObj]] = []

        # Monster box logic
        if len(char.monsters) == prepare.PARTY_LIMIT:
            monster_storage_callback = partial(
                open_dialog,
                self.client,
                [T.translate("menu_storage_monsters_full")],
            )
        else:
            monster_storage_callback = self._change_state(
                "MonsterStorageState", character=char
            )

        if char.monster_boxes.get_all_monsters_visible():
            menu.append(("menu_storage", monster_storage_callback))

        if len(char.monsters) > 1:
            menu.append(
                (
                    "menu_dropoff",
                    self._change_state("MonsterDropOffState", character=char),
                )
            )

        # Item box logic
        if len(char.items.get_items()) == prepare.MAX_LOCKER:
            item_storage_callback = partial(
                open_dialog,
                self.client,
                [T.translate("menu_storage_items_full")],
            )
        else:
            item_storage_callback = self._change_state(
                "ItemStorageState", character=char
            )

        if char.item_boxes.get_all_items_visible():
            menu.append(("menu_item_storage", item_storage_callback))

        if len(char.items.get_items()) > 1:
            menu.append(
                (
                    "menu_item_dropoff",
                    self._change_state("ItemDropOffState", character=char),
                )
            )

        # Other menu items
        menu.append(("menu_multiplayer", self._not_implemented_dialog))
        menu.append(("log_off", self.client.pop_state))

        # Collect items from all injected providers
        for provider in self.menu_providers:
            menu.extend(provider.get_menu_items(self.client, self.character))

        return menu


class PCState(PygameMenuState):
    """The PC State: deposit monster, deposit item, etc."""

    def __init__(
        self, character: NPC, menu_builder: Optional[PCMenuBuilder] = None
    ) -> None:
        super().__init__()
        kennel = prepare.KENNEL
        locker = prepare.LOCKER
        char = character

        # it creates the kennel and locker (new players)
        if not char.monster_boxes.has_box(kennel, "monster"):
            char.monster_boxes.create_box(kennel, "monster")
        if not char.item_boxes.has_box(locker, "item"):
            char.item_boxes.create_box(locker, "item")

        if menu_builder is None:
            self.menu_builder = PCMenuBuilder(self.client, char)
        else:
            self.menu_builder = menu_builder

        menu_items = self.menu_builder.build_menu_items()
        add_menu_items(self.menu, menu_items)

    def update_animation_size(self) -> None:
        widgets_size = self.menu.get_size(widget=True)
        self.menu.resize(
            max(1, int(widgets_size[0] * self.animation_size)),
            max(1, int(widgets_size[1] * self.animation_size)),
        )

    def animate_open(self) -> Animation:
        """Animate the menu popping in."""
        self.animation_size = 0.0
        ani = self.animate(self, animation_size=1.0, duration=0.2)
        ani.schedule(self.update_animation_size, ScheduleType.ON_UPDATE)
        return ani
