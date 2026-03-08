# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
"""This module contains the Start state."""

from __future__ import annotations

import logging
from collections.abc import Callable
from functools import partial
from typing import TYPE_CHECKING, Any, ClassVar

from pygame.surface import Surface
from pygame_menu.locals import ALIGN_CENTER, POSITION_EAST
from pygame_menu.menu import Menu

from tuxemon.database.runtime import db
from tuxemon.launcher import GameLauncher
from tuxemon.locale.locale import T
from tuxemon.menu.menu import PygameMenuState
from tuxemon.platform.const.graphics import BG_START_SCREEN, BLACK_COLOR
from tuxemon.session import local_session
from tuxemon.state.state import State
from tuxemon.tools import open_dialog

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient

logger = logging.getLogger(__name__)


class BackgroundState(State):
    """
    Background state is used to prevent other states from
    being required to track dirty screen areas. For example,
    in the start state, there is a menu on a blank background,
    since menus do not clean up dirty areas, the blank,
    "Background state" will do that. The alternative is creating
    a system for states to clean up their dirty screen areas.

    Eventually the need for this will be phased out.
    """

    name: ClassVar[str] = "BackgroundState"

    def __init__(self, client: BaseClient, *args: Any, **kwargs: Any):
        super().__init__(client, *args, **kwargs)

    def draw(self, surface: Surface) -> None:
        surface.fill(BLACK_COLOR)


class StartState(PygameMenuState):
    """The state responsible for the start menu."""

    name: ClassVar[str] = "StartState"

    def add_menu_items(
        self,
        menu: Menu,
    ) -> None:
        def new_game() -> None:
            if not self.client.solana_manager.has_wallet_connection():
                open_dialog(
                    self.client,
                    [
                        "Connect a Phantom/Solflare wallet or import/create a dev wallet first."
                    ],
                )
                return

            if not self.client.network_manager.is_connected():
                open_dialog(
                    self.client,
                    [
                        "SolaMon is multiplayer-only. Host or join a game first."
                    ],
                )
                return

            launcher = GameLauncher(self.client)
            launcher.launch(
                session=local_session,
                meta=db.mod_metadata.get_mod_metadata(
                    self.client.config.mods[0]
                ),
                remove_states=["StartState"],
            )

        def connect_phantom() -> None:
            self._connect_provider("phantom")

        def connect_solflare() -> None:
            self._connect_provider("solflare")

        def import_private_key() -> None:
            self.client.push_state(
                "InputMenu",
                prompt="Paste private key JSON array (32 or 64 bytes)",
                callback=self._import_private_key,
            )

        def create_wallet() -> None:
            ok, message = self.client.solana_manager.create_devnet_wallet()
            open_dialog(self.client, [message])
            if ok:
                self._show_connected_wallet()

        def change_state(
            state: State | str, **kwargs: Any
        ) -> Callable[[], None]:
            def _change() -> None:
                self.unsubscribe(
                    "afk.threshold_reached", self._on_afk_threshold
                )
                self.client.push_state(state, **kwargs)

            return _change

        def exit_game() -> None:
            self.client.quit()

        menu.add.button(
            title="CONNECT PHANTOM",
            action=connect_phantom,
            font_size=self.font_type.big,
            button_id="solamon_wallet_connect_phantom",
        )
        menu.add.button(
            title="CONNECT SOLFLARE",
            action=connect_solflare,
            font_size=self.font_type.big,
            button_id="solamon_wallet_connect_solflare",
        )
        menu.add.button(
            title="IMPORT PRIVATE KEY",
            action=import_private_key,
            font_size=self.font_type.big,
            button_id="solamon_wallet_import",
        )
        menu.add.button(
            title="CREATE DEVNET WALLET",
            action=create_wallet,
            font_size=self.font_type.big,
            button_id="solamon_wallet_create",
        )
        menu.add.button(
            title=T.translate("menu_multiplayer"),
            action=change_state("MultiplayerMenu"),
            font_size=self.font_type.big,
            button_id="menu_multiplayer",
        )
        menu.add.button(
            title="PLAY SOLAMON",
            action=new_game,
            font_size=self.font_type.big,
            button_id="menu_new_game",
        )
        menu.add.button(
            title=T.translate("menu_options"),
            action=change_state("ControlState", main_menu=True),
            font_size=self.font_type.big,
            button_id="menu_options",
        )
        menu.add.button(
            title=T.translate("exit"),
            action=exit_game,
            font_size=self.font_type.big,
            button_id="exit",
        )

    def _connect_provider(self, provider: str) -> None:
        ok, message = self.client.solana_manager.connect_wallet_provider(
            provider
        )
        open_dialog(self.client, [message])
        if ok:
            self._show_connected_wallet()

    def _import_private_key(self, private_key_payload: str) -> None:
        ok, message = self.client.solana_manager.import_private_key(
            private_key_payload
        )
        open_dialog(self.client, [message])
        if ok:
            self._show_connected_wallet()

    def _show_connected_wallet(self) -> None:
        wallet = self.client.solana_manager.wallet_address
        if wallet:
            open_dialog(
                self.client,
                [f"Connected wallet: {wallet[:4]}...{wallet[-4:]}"],
            )

    def __init__(self, client: BaseClient, **kwargs: Any) -> None:
        width, height = client.context.resolution

        super().__init__(client=client, height=height, width=width, **kwargs)

        theme = self._setup_theme(BG_START_SCREEN)
        theme.scrollarea_position = POSITION_EAST
        theme.widget_alignment = ALIGN_CENTER
        self._menu_config["theme"] = theme

        self.escape_key_exits = False
        self.client.afk_manager.add_threshold("IntroState", 15.0)
        self.event_bus.subscribe(
            "afk.threshold_reached", self._on_afk_threshold, priority=10
        )

        self.add_menu_items(self.menu)
        self.reset_theme()

    def _on_afk_threshold(self, level: str) -> None:
        if level == "IntroState":
            self.client.replace_state("IntroState")

    def shutdown(self) -> None:
        self.unsubscribe("afk.threshold_reached", self._on_afk_threshold)
        super().shutdown()


class ModsChoice(PygameMenuState):
    """The state responsible for the mods menu."""

    name: ClassVar[str] = "ModsChoice"

    def add_menu_items(
        self,
        menu: Menu,
    ) -> None:

        def new_game(mod_name: str) -> None:
            launcher = GameLauncher(self.client)
            launcher.launch(
                session=local_session,
                meta=db.mod_metadata.get_mod_metadata(mod_name),
                remove_states=["StartState", "ModsChoice"],
            )

        for mod_name in self.mods:
            menu.add.button(
                title=T.translate(f"{mod_name}_campaign"),
                action=partial(new_game, mod_name),
                font_size=self.font_type.big,
                button_id=mod_name,
            )

    def __init__(
        self, client: BaseClient, mods: list[str], **kwargs: Any
    ) -> None:
        self.mods = mods
        width, height = client.context.resolution

        super().__init__(client=client, height=height, width=width, **kwargs)

        theme = self._setup_theme(BG_START_SCREEN)
        theme.scrollarea_position = POSITION_EAST
        theme.widget_alignment = ALIGN_CENTER
        self._menu_config["theme"] = theme

        self.add_menu_items(self.menu)
        self.reset_theme()
