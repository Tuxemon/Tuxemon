# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from functools import partial
from typing import TYPE_CHECKING, Any

from tuxemon.item.filter import ItemFilter
from tuxemon.locale.locale import T
from tuxemon.save_system.save_slots import save_index_to_ui
from tuxemon.session import local_session
from tuxemon.world.menu_flags import MenuFlags

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient
    from tuxemon.entity.npc import NPC
    from tuxemon.states.world_menus import WorldMenuState

logger = logging.getLogger(__name__)


WorldMenuGameObj = Callable[[], object]


@dataclass
class MenuItem:
    key: str  # internal ID, not the label
    label: str
    callback: WorldMenuGameObj
    enabled: bool = True


class WorldMenuManager:
    """Manages persistent menu items and builds the dynamic world menu."""

    def __init__(self, client: BaseClient) -> None:
        self.menu_flags = MenuFlags()
        self.menu_items: list[MenuItem] = []
        self.menu_renderer: WorldMenuState | None = None
        self.client = client

    def set_menu_renderer(self, menu_renderer: WorldMenuState) -> None:
        """Links the menu manager to a WorldMenuState instance."""
        self.menu_renderer = menu_renderer

    def set_item_enabled(self, key: str, enabled: bool) -> None:
        """Enables or disables a menu item by its key, if it exists."""
        for i, item in enumerate(self.menu_items):
            if item.key == key:
                self.menu_items[i] = MenuItem(
                    key=item.key,
                    label=item.label,
                    callback=item.callback,
                    enabled=enabled,
                )
                self.update_menu_display()
                return

    def update_item(
        self,
        key: str,
        new_callback: WorldMenuGameObj | None = None,
        enabled: bool | None = None,
    ) -> None:
        """Updates an item's callback and/or enabled state by key."""
        for i, item in enumerate(self.menu_items):
            if item.key == key:
                self.menu_items[i] = MenuItem(
                    key=item.key,
                    label=item.label,
                    callback=new_callback or item.callback,
                    enabled=enabled if enabled is not None else item.enabled,
                )
                self.update_menu_display()
                return

    def item_exists(
        self, key: str, include_dynamic: list[MenuItem] | None = None
    ) -> bool:
        """
        Checks if an item with the translated key exists in the persistent
        or provided menu items.
        """
        label = T.translate(key).upper()
        all_items = self.menu_items + (include_dynamic or [])
        return any(item.label == label for item in all_items)

    def add_item(
        self, key: str, callback: WorldMenuGameObj, position: int = -1
    ) -> None:
        """Adds or updates a menu item to the manager's persistent list."""
        if self.item_exists(key):
            return

        label = T.translate(key).upper()
        new_item = MenuItem(key, label, callback)

        if position == -1 or position >= len(self.menu_items):
            self.menu_items.append(new_item)
        else:
            self.menu_items.insert(position, new_item)

        self.update_menu_display()

    def remove_item(self, key: str) -> None:
        """
        Removes a menu item by its label key from the manager's persistent list.
        """
        label = T.translate(key).upper()
        initial_len = len(self.menu_items)

        self.menu_items = [
            item for item in self.menu_items if item.label != label
        ]

        if len(self.menu_items) < initial_len:
            self.update_menu_display()

    def update_menu_display(self) -> None:
        """Notifies the linked WorldMenuState to refresh its display."""
        if self.menu_renderer:
            self.menu_renderer.update_menu_from_manager()

    def _get_change_state_callback(
        self, state: str, **kwargs: Any
    ) -> Callable[[], object]:
        """Helper to create state change callbacks."""
        return partial(self.client.push_state, state, **kwargs)

    def _get_exit_game_callback(self) -> Callable[[], None]:
        """Helper to create exit game callback."""
        return lambda: self.client.event_engine.execute_action("quit_world")

    def _menu_item(self, key: str, state: str, **kwargs: Any) -> MenuItem:
        label = T.translate(key).upper()
        callback = self._get_change_state_callback(state, **kwargs)
        return MenuItem(key, label, callback)

    def _insert_item_specific_entries_in_menu(
        self, player: NPC, current_menu: list[MenuItem]
    ) -> None:
        """
        Inserts item-specific menu entries into the current_menu at their
        defined positions.
        """
        entries: list[tuple[int, MenuItem]] = []

        for itm in player.items:
            dm = itm.dynamic_menu
            if (
                dm
                and dm.menu_type == "world"
                and all(
                    hasattr(dm, attr)
                    for attr in ["position", "label_key", "state", "enabled"]
                )
            ):
                if dm.enabled and dm.label_key not in self.menu_flags._flags:
                    self.menu_flags.set_enabled(dm.label_key, True)

                if not self.menu_flags.is_enabled(dm.label_key):
                    continue

                if not self.item_exists(dm.label_key, current_menu):
                    label = T.translate(dm.label_key).upper()
                    callback = self._get_change_state_callback(
                        dm.state, character=player
                    )
                    entries.append(
                        (dm.position, MenuItem(dm.label_key, label, callback))
                    )

        # Sort and insert to avoid position shifting issues
        for pos, item in sorted(entries, key=lambda x: x[0]):
            # Cap position to avoid out-of-bounds
            insert_at = min(pos, len(current_menu))
            current_menu.insert(insert_at, item)

    def _merge_persistent_items(
        self, current_menu: list[MenuItem]
    ) -> list[MenuItem]:
        """
        Appends persistent menu items, ensuring no duplicate labels are added.
        """
        return [
            item
            for item in self.menu_items
            if not self.item_exists(item.label, current_menu)
        ]

    def build_current_menu_items(self, player: NPC) -> list[MenuItem]:
        """
        Builds the complete list of menu items based on the player's state
        and any globally managed items.
        """
        if self.menu_renderer is None:
            logger.error(
                "WorldMenuManager: menu_renderer is not set. Returning empty menu."
            )
            return []

        param = {"character": player}
        current_menu: list[MenuItem] = []

        if player.monsters and self.menu_flags.is_enabled("menu_monster"):
            current_menu.append(
                MenuItem(
                    "menu_monster",
                    T.translate("menu_monster").upper(),
                    self.menu_renderer.open_monster_menu,
                )
            )

        if player.items and self.menu_flags.is_enabled("menu_bag"):
            items_filtered = ItemFilter(player.items)
            items_filtered.set_filter_all_visible()
            current_menu.append(
                self._menu_item(
                    "menu_bag",
                    "ItemMenuState",
                    character=player,
                    source="WorldMenuState",
                    item_filter=items_filtered,
                )
            )

        if self.menu_flags.is_enabled("menu_player"):
            current_menu.append(
                self._menu_item("menu_player", "CharacterState", **param)
            )

        if player.mission_controller.get_missions_with_met_prerequisites():
            current_menu.append(
                self._menu_item(
                    "menu_missions", "MissionState", character=player
                )
            )

        if self.menu_flags.is_enabled("menu_save"):
            slot = local_session.current_slot
            idx = save_index_to_ui(slot) if slot else 0
            current_menu.append(
                self._menu_item("menu_save", "SaveMenuState", selected_index=idx)
            )

        if self.menu_flags.is_enabled("menu_load"):
            slot = local_session.current_slot
            idx = save_index_to_ui(slot) if slot else 0
            current_menu.append(
                self._menu_item("menu_load", "LoadMenuState", selected_index=idx)
            )

        current_menu.append(self._menu_item("menu_options", "ControlState"))

        current_menu.append(
            MenuItem(
                "exit",
                T.translate("exit").upper(),
                self._get_exit_game_callback(),
            )
        )

        self._insert_item_specific_entries_in_menu(player, current_menu)
        current_menu.extend(self._merge_persistent_items(current_menu))
        return current_menu
