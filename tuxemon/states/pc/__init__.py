# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Callable
from functools import partial
from typing import Any

import pygame_menu

from tuxemon import prepare
from tuxemon.animation import Animation
from tuxemon.locale import T
from tuxemon.menu.menu import PygameMenuState
from tuxemon.session import local_session
from tuxemon.state import State
from tuxemon.states.pc_kennel import HIDDEN_LIST
from tuxemon.states.pc_locker import HIDDEN_LIST_LOCKER
from tuxemon.tools import open_dialog

MenuGameObj = Callable[[], object]


def add_menu_items(
    menu: pygame_menu.Menu,
    items: list[tuple[str, MenuGameObj]],
) -> None:
    for key, callback in items:
        label = T.translate(key).upper()
        menu.add.button(label, callback)


def not_implemented_dialog() -> None:
    open_dialog(local_session, [T.translate("not_implemented")])


class PCState(PygameMenuState):
    """The PC State: deposit monster, deposit item, etc."""

    def __init__(self) -> None:
        super().__init__()
        kennel = prepare.KENNEL
        locker = prepare.LOCKER
        player = local_session.player

        # it creates the kennel and locker (new players)
        if not player.monster_boxes.has_box(kennel, "monster"):
            player.monster_boxes.create_box(kennel, "monster")
        if not player.item_boxes.has_box(locker, "item"):
            player.item_boxes.create_box(locker, "item")

        def change_state(state: str, **kwargs: Any) -> partial[State]:
            return partial(self.client.replace_state, state, **kwargs)

        # monster boxes
        if len(player.monsters) == player.party_limit:
            storage = partial(
                open_dialog,
                local_session,
                [T.translate("menu_storage_monsters_full")],
            )
        else:
            storage = change_state("MonsterStorageState")

        dropoff = change_state("MonsterDropOffState")

        # item boxes
        if len(player.items) == prepare.MAX_LOCKER:
            storage = partial(
                open_dialog,
                local_session,
                [T.translate("menu_storage_items_full")],
            )
        else:
            item_storage = change_state("ItemStorageState")

        item_dropoff = change_state("ItemDropOffState")

        multiplayer = change_state("MultiplayerMenu")

        nr_monsters = len(player.monster_boxes.get_all_monsters_visible())
        nr_items = len(player.item_boxes.get_all_items_visible())

        menu: list[tuple[str, MenuGameObj]] = []
        if nr_monsters > 0:
            menu.append(("menu_storage", storage))
        if len(player.monsters) > 1:
            menu.append(("menu_dropoff", dropoff))
        if nr_items > 0:
            menu.append(("menu_item_storage", item_storage))
        if len(player.items) > 1:
            menu.append(("menu_item_dropoff", item_dropoff))
        # replace multiplayer when fixed
        menu.append(("menu_multiplayer", not_implemented_dialog))
        menu.append(("log_off", self.client.pop_state))

        add_menu_items(self.menu, menu)

    def update_animation_size(self) -> None:
        widgets_size = self.menu.get_size(widget=True)
        self.menu.resize(
            max(1, int(widgets_size[0] * self.animation_size)),
            max(1, int(widgets_size[1] * self.animation_size)),
        )

    def animate_open(self) -> Animation:
        """
        Animate the menu popping in.

        Returns:
            Popping in animation.

        """
        self.animation_size = 0.0

        ani = self.animate(self, animation_size=1.0, duration=0.2)
        ani.update_callback = self.update_animation_size

        return ani
