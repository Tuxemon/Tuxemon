# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Callable, Generator
from typing import TYPE_CHECKING, Any, ClassVar

from pygame_menu.menu import Menu

from tuxemon.locale.locale import T
from tuxemon.menu.interface import MenuItem
from tuxemon.menu.menu import PopUpMenu, PygameMenuState
from tuxemon.menu.transitions import PopInClamped
from tuxemon.tools import open_dialog

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient

MenuGameObj = Callable[[], object]


def add_menu_items(menu: Menu, items: list[tuple[str, MenuGameObj]]) -> None:
    for key, callback in items:
        label = T.translate(key).upper()
        menu.add.button(label, callback)


class MultiplayerMenu(PygameMenuState):
    """MP Menu, updated for asynchronous WebSockets."""

    name: ClassVar[str] = "MultiplayerMenu"
    shrink_to_items = True

    def __init__(self, client: BaseClient, **kwargs: Any) -> None:
        super().__init__(client=client, transition=PopInClamped(), **kwargs)

        self.network = self.client.network_manager

        menu: list[tuple[str, MenuGameObj]] = []
        menu.append(("multiplayer_host_game", self.host_game))
        menu.append(("multiplayer_scan_games", self.load_server_list))
        menu.append(("multiplayer_join_game", self.join_by_ip))

        add_menu_items(self.menu, menu)

    def host_game(self) -> None:
        """Starts the local server and attempts to connect the client to it."""
        assert self.network.client
        assert self.network.server

        if self.network.server.listening:
            self.client.pop_state(self)
            open_dialog(
                self.client, [T.translate("multiplayer_already_hosting")]
            )
            return

        self.network.server.listening = True
        self.network.client.connect_to_host(
            "127.0.0.1",
            self.network.server.server_port,
        )
        self.client.pop_state(self)
        open_dialog(self.client, [T.translate("multiplayer_hosting_ready")])

    def load_server_list(self) -> None:
        """Loads the hardcoded server list and opens the selection menu."""
        assert self.network.client
        if not self.network.is_host():
            self.network.client.update_multiplayer_list()

        self.client.push_state("MultiplayerSelect")

    def join_by_ip(self) -> None:
        """Pushes an input menu to get the IP/Port from the user."""
        self.client.push_state(
            "InputMenu", prompt=T.translate("multiplayer_join_prompt")
        )

    def join(self) -> None:
        """
        Enables the client connection attempt based on a pre-selected game.
        This is typically called *after* MultiplayerSelect/InputMenu provides an IP.
        """
        assert self.network.client
        if self.network.is_host():
            return
        else:
            if self.network.client.selected_game:
                ip, port = self.network.client.selected_game
                self.network.client.connect_to_host(ip, port)


class MultiplayerSelect(PopUpMenu[None]):
    """Menu to show games found by the network game scanner"""

    name: ClassVar[str] = "MultiplayerSelect"
    shrink_to_items = True

    def __init__(self, client: BaseClient, **kwargs: Any) -> None:
        super().__init__(client=client, **kwargs)
        self.network = self.client.network_manager

        # make a timer to refresh the menu items every second
        self.task(self.reload_items, interval=1, times=-1)

    def initialize_items(self) -> Generator[MenuItem[None], None, None]:
        assert self.network.client
        servers = self.network.client.server_list
        if servers:
            for server in servers:
                label = self.shadow_text(server)
                yield MenuItem(label, None, None, None)
        else:
            label = self.shadow_text(T.translate("multiplayer_no_servers"))
            item = MenuItem(label, None, None, None)
            item.enabled = False
            yield item
