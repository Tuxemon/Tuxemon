# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Callable
from functools import partial
from typing import TYPE_CHECKING, ClassVar

from tuxemon.locale.locale import T
from tuxemon.platform.const.sizes import MAX_LOCKER
from tuxemon.tools import open_dialog

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient
    from tuxemon.entity.npc import NPC

MenuGameObj = Callable[[], object]


class PCMenuRegistry:
    """Global registry to manage PC feature expansion."""

    _providers: list[MenuProvider] = []

    @classmethod
    def register(cls, provider: MenuProvider) -> None:
        """Register a new feature provider."""
        cls._providers.append(provider)

    @classmethod
    def get_for_tag(cls, tag: str) -> list[MenuProvider]:
        """Return providers matching a specific PC type/tag."""
        return [p for p in cls._providers if tag in p.target_tags]


class MenuProvider:
    """Base class for adding dynamic content to the PC menu."""

    target_tags: list[str] = ["standard"]

    def get_menu_items(
        self,
        client: BaseClient,
        character: NPC,
        tag_list: list[str],
    ) -> list[tuple[str, MenuGameObj]]:
        raise NotImplementedError


class CalendarProvider(MenuProvider):
    name: ClassVar[str] = "menu_calendar"
    target_tags = ["calendar"]

    def get_menu_items(
        self,
        client: BaseClient,
        character: NPC,
        tag_list: list[str],
    ) -> list[tuple[str, MenuGameObj]]:
        return [
            (
                "menu_calendar",
                partial(
                    client.push_state,
                    "CalendarState",
                    session=character.session,
                ),
            )
        ]


class EmailProvider(MenuProvider):
    name: ClassVar[str] = "menu_email"
    target_tags = ["email"]

    def get_menu_items(
        self,
        client: BaseClient,
        character: NPC,
        tag_list: list[str],
    ) -> list[tuple[str, MenuGameObj]]:
        return [
            (
                "menu_email",
                partial(
                    client.push_state,
                    "EmailState",
                    character=character,
                    tag_list=tag_list,
                ),
            )
        ]


PCMenuRegistry.register(CalendarProvider())
PCMenuRegistry.register(EmailProvider())


class PCMenuBuilder:
    def __init__(
        self,
        client: BaseClient,
        character: NPC,
        menu_providers: list[MenuProvider] | None = None,
        tag_list: list[str] | None = None,
    ) -> None:
        self.client = client
        self.character = character
        self.menu_providers = menu_providers or []
        self.tag_list = tag_list or []

    def build_menu_items(self) -> list[tuple[str, MenuGameObj]]:
        char = self.character
        menu: list[tuple[str, MenuGameObj]] = []

        monster_callback = partial(
            self.client.replace_state, "MonsterStorageState", character=char
        )
        if char.monster_boxes.get_all_monsters_visible():
            menu.append(("menu_storage", monster_callback))

        # Monster drop-off
        if len(char.monsters) > 1:
            menu.append(
                (
                    "menu_dropoff",
                    partial(
                        self.client.replace_state,
                        "MonsterDropOffState",
                        character=char,
                    ),
                )
            )

        # --- Item Storage ---
        if len(char.items) == MAX_LOCKER:
            item_callback = partial(
                open_dialog,
                self.client,
                [T.translate("menu_storage_items_full")],
            )
        else:
            item_callback = partial(
                self.client.replace_state, "ItemStorageState", character=char
            )

        if char.item_boxes.get_all_items_visible():
            menu.append(("menu_item_storage", item_callback))

        # Item drop-off
        if len(char.items) > 1:
            menu.append(
                (
                    "menu_item_dropoff",
                    partial(
                        self.client.replace_state,
                        "ItemDropOffState",
                        character=char,
                    ),
                )
            )

        # --- Dynamic Providers ---
        for provider in self.menu_providers:
            menu.extend(
                provider.get_menu_items(self.client, char, self.tag_list)
            )

        # --- Multiplayer placeholder ---
        menu.append(
            (
                "menu_multiplayer",
                partial(
                    open_dialog, self.client, [T.translate("not_implemented")]
                ),
            )
        )

        # --- Log Off ---
        menu.append(("log_off", self.client.pop_state))

        return menu
