# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Callable, Generator
from functools import partial
from typing import TYPE_CHECKING, Any, ClassVar

from pygame_menu.menu import Menu

from tuxemon.animation import Animation, ScheduleType
from tuxemon.locale.locale import T
from tuxemon.menu.interface import MenuItem
from tuxemon.menu.menu import PopUpMenu, PygameMenuState
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
        super().__init__(client=client, **kwargs)
        self.network = self.client.network_manager

        menu: list[tuple[str, MenuGameObj]] = []
        menu.append(("multiplayer_host_game", self.host_game))
        menu.append(("multiplayer_scan_games", self.load_server_list))
        menu.append(("multiplayer_join_game", self.join_by_ip))

        add_menu_items(self.menu, menu)

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

        self.network.server.start_hosting()
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
            "InputMenu",
            prompt=T.translate("multiplayer_join_prompt"),
            callback=self._join_by_ip_callback,
        )

    def _join_by_ip_callback(self, text: str) -> None:
        assert self.network.client
        raw = text.strip()
        if not raw:
            open_dialog(self.client, [T.translate("multiplayer_join_prompt")])
            return

        host = raw
        port = 40081
        if ":" in raw:
            host_part, port_part = raw.rsplit(":", 1)
            host = host_part.strip() or host
            try:
                port = int(port_part.strip())
            except ValueError:
                open_dialog(self.client, ["Invalid port. Use ip:port"])
                return

        self.network.client.selected_game = (host, port)
        self.join()

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
            for index, server in enumerate(servers):
                label = self.shadow_text(server)
                yield MenuItem(
                    label,
                    None,
                    None,
                    partial(self._join_selected_server, index),
                )
        else:
            label = self.shadow_text(T.translate("multiplayer_no_servers"))
            item = MenuItem(label, None, None, None)
            item.enabled = False
            yield item

    def _join_selected_server(self, index: int) -> None:
        assert self.network.client
        if index >= len(self.network.client.available_games):
            return

        self.network.client.selected_game = (
            self.network.client.available_games[index]
        )
        ip, port = self.network.client.selected_game
        self.network.client.connect_to_host(ip, port)
        self.client.pop_state(self)
