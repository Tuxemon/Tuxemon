# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
""" This module contains the PCState state.
"""
from __future__ import annotations

import logging
from functools import partial
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Generator,
    Optional,
    Sequence,
    Tuple,
)

import pygame_menu

from tuxemon import graphics, prepare
from tuxemon.db import db
from tuxemon.locale import T
from tuxemon.menu.input import InputMenu
from tuxemon.menu.interface import MenuItem
from tuxemon.menu.menu import Menu, PopUpMenu, PygameMenuState
from tuxemon.menu.theme import get_theme
from tuxemon.session import local_session
from tuxemon.states.monster import MonsterMenuState
from tuxemon.tools import open_dialog

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from tuxemon.animation import Animation
    from tuxemon.monster import Monster


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

    def __init__(self) -> None:
        super().__init__()

        def change_state(state: str, **kwargs: Any) -> MenuGameObj:
            return partial(self.client.replace_state, state, **kwargs)

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

        add_menu_items(
            self,
            (
                ("menu_monster", change_state("MonsterMenuState")),
                ("menu_storage", storage_callback),
                ("menu_dropoff", dropoff_callback),
                ("menu_items", change_state("ItemMenuState")),
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


class MonsterTakeState(PygameMenuState):
    """Menu for the Monster Take state.

    Shows all tuxemon currently in a storage kennel, and selecting one puts it
    into your current party."""

    def add_menu_items(
        self,
        menu: pygame_menu.Menu,
        items: Sequence[Tuple[Monster, MenuGameObj]],
    ) -> None:

        for monster, callback in items:
            label = T.translate(monster.name).upper()
            results = db.lookup(monster.slug, table="monster").dict()
            new_image = menu.add.image(
                graphics.transform_resource_filename(
                    results["sprites"]["menu1"] + ".png"
                )
            )
            new_image.scale(prepare.SCALE, prepare.SCALE)
            new_button = menu.add.button(label, callback)

    def __init__(self, box_name: str) -> None:
        width, height = prepare.SCREEN_SIZE

        theme = get_theme()
        theme.scrollarea_position = pygame_menu.locals.POSITION_EAST
        columns = 3

        self.box_name = box_name
        self.player = local_session.player
        self.box = self.player.monster_boxes[self.box_name]

        num_mons = len(self.box)
        # Widgets are like a pygame_menu label, image, etc.
        num_widgets_per_monster = 2
        rows = int(num_mons * num_widgets_per_monster / columns) + 1
        # Make sure rows are divisible by num_widgets
        while rows % num_widgets_per_monster != 0:
            rows += 1

        super().__init__(
            height=height, width=width, columns=columns, rows=rows
        )

        def take_monster(monster: Monster) -> None:
            self.player.remove_monster_from_storage(monster)
            self.player.add_monster(monster)
            open_dialog(
                local_session,
                [
                    T.format(
                        "menu_storage_take_monster", {"name": monster.name}
                    )
                ],
            )
            theme = get_theme()
            theme.scrollarea_position = (
                pygame_menu.locals.SCROLLAREA_POSITION_NONE
            )
            self.client.pop_state(self)

        def take_monster_callback(monster: Monster) -> Callable[[], object]:
            return partial(take_monster, monster)

        menu_items_map = []
        for monster in self.box:
            menu_items_map.append((monster, take_monster_callback(monster)))

        self.add_menu_items(self.menu, menu_items_map)


class MonsterBoxChooseState(PygameMenuState):
    """Menu to choose a tuxemon box."""

    def __init__(self) -> None:
        _, height = prepare.SCREEN_SIZE

        super().__init__(height=height)

        self.animation_offset = 0

        menu_items_map = self.get_menu_items_map()
        self.add_menu_items(self.menu, menu_items_map)

    def add_menu_items(
        self,
        menu: pygame_menu.Menu,
        items: Sequence[Tuple[str, MenuGameObj]],
    ) -> None:

        menu.add.vertical_fill()
        for key, callback in items:
            label = T.translate(key).upper()
            menu.add.button(label, callback)
            menu.add.vertical_fill()

        width, height = prepare.SCREEN_SIZE
        widgets_size = menu.get_size(widget=True)
        b_width, b_height = menu.get_scrollarea().get_border_size()
        menu.resize(
            widgets_size[0],
            height - 2 * b_height,
            position=(width + b_width, b_height, False),
        )

    def get_menu_items_map(self) -> Sequence[Tuple[str, MenuGameObj]]:
        """
        Return a list of menu options and callbacks, to be overridden by
        class descendents.
        """
        return []

    def change_state(self, state: str, **kwargs: Any) -> Callable[[], object]:
        return partial(self.client.replace_state, state, **kwargs)

    def update_animation_position(self) -> None:
        self.menu.translate(-self.animation_offset, 0)

    def animate_open(self) -> Animation:
        """
        Animate the menu sliding in.

        Returns:
            Sliding in animation.

        """

        width = self.menu.get_width(border=True)
        self.animation_offset = 0

        ani = self.animate(self, animation_offset=width, duration=0.50)
        ani.update_callback = self.update_animation_position

        return ani

    def animate_close(self) -> Animation:
        """
        Animate the menu sliding out.

        Returns:
            Sliding out animation.

        """
        ani = self.animate(self, animation_offset=0, duration=0.50)
        ani.update_callback = self.update_animation_position

        return ani


class MonsterBoxChooseStorageState(MonsterBoxChooseState):
    """Menu to choose a box, which you can then take a tuxemon from."""

    def get_menu_items_map(self) -> Sequence[Tuple[str, MenuGameObj]]:
        player = local_session.player
        menu_items_map = []
        for box_name, monsters in player.monster_boxes.items():
            if not monsters:
                menu_callback = partial(
                    open_dialog,
                    local_session,
                    [T.translate("menu_storage_empty_kennel")],
                )
            else:
                menu_callback = self.change_state(
                    "MonsterTakeState", box_name=box_name
                )
            menu_items_map.append((box_name, menu_callback))
        return menu_items_map


class MonsterBoxChooseDropOffState(MonsterBoxChooseState):
    """Menu to choose a box, which you can then drop off a tuxemon into."""

    def get_menu_items_map(self) -> Sequence[Tuple[str, MenuGameObj]]:
        player = local_session.player
        menu_items_map = []
        for box_name, monsters in player.monster_boxes.items():
            menu_callback = self.change_state(
                "MonsterDropOffState", box_name=box_name
            )
            menu_items_map.append((box_name, menu_callback))
        return menu_items_map


class MonsterDropOffState(MonsterMenuState):
    """Shows all Tuxemon in player's party, puts it into box if selected."""

    def __init__(self, box_name: str) -> None:
        super().__init__()

        self.box_name = box_name

    def on_menu_selection(
        self,
        menu_item: MenuItem[Optional[Monster]],
    ) -> None:
        player = local_session.player
        monster = menu_item.game_object
        assert monster

        player.monster_boxes[self.box_name].append(monster)
        player.remove_monster(monster)

        self.client.pop_state(self)
