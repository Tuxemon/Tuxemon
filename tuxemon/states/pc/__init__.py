#
# Tuxemon
# Copyright (C) 2014, William Edwards <shadowapex@gmail.com>,
#                     Benjamin Bean <superman2k5@gmail.com>
#
# This file is part of Tuxemon.
#
# Tuxemon is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Tuxemon is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Tuxemon.  If not, see <http://www.gnu.org/licenses/>.
#
# Contributor(s):
#
# William Edwards <shadowapex@gmail.com>
# Derek Clark <derekjohn.clark@gmail.com>
# Leif Theden <leif.theden@gmail.com>
#
#
# states.pc
#
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

    def startup(self, **kwargs: Any) -> None:
        super().startup(**kwargs)

        def change_state(state: str, **kwargs: Any) -> MenuGameObj:
            return partial(self.client.replace_state, state, **kwargs)

        add_menu_items(
            self,
            (
                ("menu_monsters", change_state("MonsterMenuState")),
                ("menu_items", change_state("ItemMenuState")),
                (
                    "menu_multiplayer",
                    not_implemented_dialog,
                ),  # change_state("MultiplayerMenu")),
                ("log_off", self.client.pop_state),
            ),
        )


class MultiplayerMenu(PopUpMenu[MenuGameObj]):
    """MP Menu

    code salvaged from commit 6fa20da714c7b794cbe1e8a22168fa66cda13a9e
    """

    shrink_to_items = True

    def startup(self, **kwargs: Any) -> None:
        super().startup(**kwargs)

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
        if self.game.server.listening:
            self.game.pop_state(self)
            open_dialog(
                local_session, [T.translate("multiplayer_already_hosting")]
            )

        # not hosting, so start the process
        elif not self.game.isclient:
            # Configure this game to host
            self.game.ishost = True
            self.game.server.server.listen()
            self.game.server.listening = True

            # Enable the game, so we can connect to self
            self.game.client.enable_join_multiplayer = True
            self.game.client.client.listen()
            self.game.client.listening = True

            # connect to self
            while not self.game.client.client.registered:
                self.game.client.client.autodiscover(autoregister=False)
                for game in self.game.client.client.discovered_servers:
                    self.game.client.client.register(game)

            # close this menu
            self.game.pop_state(self)

            # inform player that hosting is ready
            open_dialog(
                local_session, [T.translate("multiplayer_hosting_ready")]
            )

    def scan_for_games(self) -> None:
        # start the game scanner
        if not self.game.ishost:
            self.game.client.enable_join_multiplayer = True
            self.game.client.listening = True
            self.game.client.client.listen()

        # open menu to select games
        self.game.push_state(MultiplayerSelect)

    def join_by_ip(self) -> None:
        self.game.push_state(
            InputMenu, prompt=T.translate("multiplayer_join_prompt")
        )

    def join(self) -> None:
        if self.game.ishost:
            return
        else:
            self.game.client.enable_join_multiplayer = True
            self.game.client.listening = True
            self.game.client.game.listen()


class MultiplayerSelect(PopUpMenu[None]):
    """Menu to show games found by the network game scanner"""

    shrink_to_items = True

    def startup(self, **kwargs: Any) -> None:
        super().startup(**kwargs)

        # make a timer to refresh the menu items every second
        self.task(self.reload_items, 1, -1)

    def initialize_items(self) -> Generator[MenuItem[None], None, None]:
        servers = self.game.client.server_list
        if servers:
            for server in servers:
                label = self.shadow_text(server)
                yield MenuItem(label, None, None, None)
        else:
            label = self.shadow_text(T.translate("multiplayer_no_servers"))
            item = MenuItem(label, None, None, None)
            item.enabled = False
            yield item
