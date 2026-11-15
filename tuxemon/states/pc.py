# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026
# William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, ClassVar

from pygame_menu.menu import Menu

from tuxemon.computer import PCMenuBuilder
from tuxemon.locale.locale import T
from tuxemon.menu.menu import PygameMenuState
from tuxemon.menu.transitions import PopInClamped
from tuxemon.platform.const.sizes import KENNEL, LOCKER

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient
    from tuxemon.entity.npc import NPC


MenuGameObj = Callable[[], object]


def add_menu_items(menu: Menu, items: list[tuple[str, MenuGameObj]]) -> None:
    """Add translated menu entries to a pygame_menu.Menu."""
    for key, callback in items:
        label = T.translate(key).upper()
        menu.add.button(label, callback)


class PCState(PygameMenuState):
    """
    The PC State: deposit monsters, deposit items, and any dynamic
    menu entries provided by registered PC menu providers.

    This state receives a PCMenuBuilder instance (injected by
    AccessPCAction) and uses it to populate the menu.
    """

    name: ClassVar[str] = "PCState"

    def __init__(
        self,
        client: BaseClient,
        character: NPC,
        tag_list: list[str],
        menu_builder: PCMenuBuilder | None = None,
        **kwargs: Any,
    ) -> None:
        self.tag_list = tag_list

        super().__init__(client=client, transition=PopInClamped(), **kwargs)

        self.escape_key_exits = False

        char = character

        if not char.monster_boxes.has_box(KENNEL, "monster"):
            char.monster_boxes.create_box(KENNEL)

        if not char.item_boxes.has_box(LOCKER, "item"):
            char.item_boxes.create_box(LOCKER)

        if menu_builder is None:
            menu_builder = PCMenuBuilder(
                self.client, char, menu_providers=[], tag_list=self.tag_list
            )

        self.menu_builder = menu_builder

        menu_items = self.menu_builder.build_menu_items()
        add_menu_items(self.menu, menu_items)
