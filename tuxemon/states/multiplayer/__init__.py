# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Callable, Generator

import pygame_menu

from tuxemon.animation import Animation
from tuxemon.locale import T
from tuxemon.menu.input import InputMenu
from tuxemon.menu.interface import MenuItem
from tuxemon.menu.menu import PopUpMenu, PygameMenuState
from tuxemon.session import local_session
from tuxemon.tools import open_dialog

MenuGameObj = Callable[[], object]


def add_menu_items(
    menu: pygame_menu.Menu,
    items: list[tuple[str, MenuGameObj]],
) -> None:
    for key, callback in items:
        label = T.translate(key).upper()
        menu.add.button(label, callback)


class MultiplayerMenu(PygameMenuState):
    """MP Menu

    code salvaged from commit 6fa20da714c7b794cbe1e8a22168fa66cda13a9e
    """

    shrink_to_items = True

    def __init__(self) -> None:
        super().__init__()

        menu: list[tuple[str, MenuGameObj]] = []
        menu.append(("multiplayer_host_game", self.host_game))
        menu.append(("multiplayer_scan_games", self.scan_for_games))
        menu.append(("multiplayer_join_game", self.join_by_ip))

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
