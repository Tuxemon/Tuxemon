# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
""" This module contains the PCState state.
"""
from __future__ import annotations

import logging
from functools import partial
from typing import Any, Callable, Generator, Sequence, Tuple

from tuxemon.locale import T
from tuxemon.menu.input import InputMenu
from tuxemon.menu.interface import MenuItem
from tuxemon.menu.menu import Menu, PopUpMenu
from tuxemon.session import local_session
from tuxemon.tools import open_dialog

logger = logging.getLogger(__name__)


MenuGameObj = Callable[[], object]

KENNEL = "Kennel"
LOCKER = "Locker"


def add_menu_items(
    state: Menu[MenuGameObj],
    items: Sequence[Tuple[str, MenuGameObj]],
) -> None:
    for key, callback in items:
        label = T.translate(key).upper()

        state.build_item(label, callback)


def not_implemented_dialog() -> None:
    open_dialog(local_session, [T.translate("not_implemented")])


class PCState(PopUpMenu[MenuGameObj]):
    """The state responsible in game settings."""

    shrink_to_items = True

    def __init__(self) -> None:
        super().__init__()

        # it creates the kennel and locker (new players)
        if KENNEL not in local_session.player.monster_boxes.keys():
            local_session.player.monster_boxes[KENNEL] = []
        if LOCKER not in local_session.player.item_boxes.keys():
            local_session.player.item_boxes[LOCKER] = []

        def change_state(state: str, **kwargs: Any) -> MenuGameObj:
            return partial(self.client.replace_state, state, **kwargs)

        # monster boxes
        if len(local_session.player.monsters) == 6:
            storage_callback = partial(
                open_dialog,
                local_session,
                [T.translate("menu_storage_monsters_full")],
            )
        else:
            storage_callback = change_state("MonsterBoxChooseStorageState")

        if len(local_session.player.monsters) <= 1:
            dropoff_callback = partial(
                open_dialog,
                local_session,
                [T.translate("menu_dropoff_no_monsters")],
            )
        else:
            dropoff_callback = change_state("MonsterBoxChooseDropOffState")

        # item boxes
        if len(local_session.player.items) == 30:
            storage_callback = partial(
                open_dialog,
                local_session,
                [T.translate("menu_storage_items_full")],
            )
        else:
            item_storage_callback = change_state("ItemBoxChooseStorageState")

        item_dropoff_callback = change_state("ItemBoxChooseDropOffState")

        add_menu_items(
            self,
            (
                ("menu_storage", storage_callback),
                ("menu_dropoff", dropoff_callback),
                ("menu_item_storage", item_storage_callback),
                ("menu_item_dropoff", item_dropoff_callback),
                (
                    "menu_multiplayer",
                    not_implemented_dialog,
                ),  # change_state("MultiplayerMenu")),
                ("log_off", self.client.pop_state),
            ),
        )


# unused
class MultiplayerMenu(PopUpMenu[MenuGameObj]):
    """MP Menu

    code salvaged from commit 6fa20da714c7b794cbe1e8a22168fa66cda13a9e
    """

    shrink_to_items = True

    def __init__(self) -> None:
        super().__init__()

        add_menu_items(
            self,
            (
                ("multiplayer_host_game", self.host_game),
                ("multiplayer_scan_games", self.scan_for_games),
                ("multiplayer_join_game", self.join_by_ip),
            ),
        )

    def host_game(self) -> None:

        # check if server is already hosting a game
        if self.client.server.listening:
            self.client.pop_state(self)
            open_dialog(
                local_session, [T.translate("multiplayer_already_hosting")]
            )

        # not hosting, so start the process
        elif not self.client.isclient:
            # Configure this game to host
            self.client.ishost = True
            self.client.server.server.listen()
            self.client.server.listening = True

            # Enable the game, so we can connect to self
            self.client.client.enable_join_multiplayer = True
            self.client.client.client.listen()
            self.client.client.listening = True

            # connect to self
            while not self.client.client.client.registered:
                self.client.client.client.autodiscover(autoregister=False)
                for game in self.client.client.client.discovered_servers:
                    self.client.client.client.register(game)

            # close this menu
            self.client.pop_state(self)

            # inform player that hosting is ready
            open_dialog(
                local_session, [T.translate("multiplayer_hosting_ready")]
            )

    def scan_for_games(self) -> None:
        # start the game scanner
        if not self.client.ishost:
            self.client.client.enable_join_multiplayer = True
            self.client.client.listening = True
            self.client.client.client.listen()

        # open menu to select games
        self.client.push_state(MultiplayerSelect())

    def join_by_ip(self) -> None:
        self.client.push_state(
            InputMenu(prompt=T.translate("multiplayer_join_prompt"))
        )

    def join(self) -> None:
        if self.client.ishost:
            return
        else:
            self.client.client.enable_join_multiplayer = True
            self.client.client.listening = True
            # self.client.client.game.listen()  # "LocalPygameClient" has no attribute "listen"


class MultiplayerSelect(PopUpMenu[None]):
    """Menu to show games found by the network game scanner"""

    shrink_to_items = True

    def __init__(self) -> None:
        super().__init__()

        # make a timer to refresh the menu items every second
        self.task(self.reload_items, 1, -1)

    def initialize_items(self) -> Generator[MenuItem[None], None, None]:
        servers = self.client.client.server_list
        if servers:
            for server in servers:
                label = self.shadow_text(server)
                yield MenuItem(label, None, None, None)
        else:
            label = self.shadow_text(T.translate("multiplayer_no_servers"))
            item = MenuItem(label, None, None, None)
            item.enabled = False
            yield item
