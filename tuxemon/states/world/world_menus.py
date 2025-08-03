# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from functools import partial
from typing import TYPE_CHECKING, Any, Optional

import pygame_menu

from tuxemon import prepare
from tuxemon.animation import ScheduleType
from tuxemon.item.filter import ItemFilter
from tuxemon.locale import T
from tuxemon.menu.menu import PygameMenuState
from tuxemon.platform.const import buttons
from tuxemon.platform.events import PlayerInput
from tuxemon.states.monster import MonsterMenuHandler
from tuxemon.states.world.world_menu_flags import MenuFlags

if TYPE_CHECKING:
    from tuxemon.animation import Animation
    from tuxemon.client import LocalPygameClient
    from tuxemon.npc import NPC

logger = logging.getLogger(__name__)


WorldMenuGameObj = Callable[[], object]


@dataclass
class MenuItem:
    key: str  # internal ID, not the label
    label: str
    callback: WorldMenuGameObj
    enabled: bool = True


def add_menu_items_to_pygame_menu(
    menu: pygame_menu.Menu,
    items: list[MenuItem],
) -> None:
    """Helper function to add items to a pygame_menu.Menu instance."""
    menu.clear()
    menu.add.vertical_fill()

    for item in items:
        label = item.label
        callback = item.callback
        if item.enabled:
            menu.add.button(label, callback)
        else:
            menu.add.label(
                label,
                font_color=prepare.DIMGRAY_COLOR,
            )
        menu.add.vertical_fill()

    width, height = prepare.SCREEN_SIZE
    widgets_size = menu.get_size(widget=True)
    b_width, b_height = menu.get_scrollarea().get_border_size()
    menu.resize(
        widgets_size[0],
        height - 2 * b_height,
        position=(width + b_width, b_height, False),
    )


class WorldMenuManager:
    """Manages persistent menu items and builds the dynamic world menu."""

    def __init__(self, client: LocalPygameClient) -> None:
        self.menu_flags = MenuFlags()
        self.menu_items: list[MenuItem] = []
        self.menu_renderer: Optional[WorldMenuState] = None
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
        new_callback: Optional[WorldMenuGameObj] = None,
        enabled: Optional[bool] = None,
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
        self, key: str, include_dynamic: Optional[list[MenuItem]] = None
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
        return lambda: self.client.event_engine.execute_action("quit")

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

        for itm in player.items.get_items():
            wm = itm.world_menu
            if wm and all(
                hasattr(wm, attr)
                for attr in ["position", "label_key", "state", "enabled"]
            ):
                if wm.enabled and wm.label_key not in self.menu_flags._flags:
                    self.menu_flags.set_enabled(wm.label_key, True)

                if not self.menu_flags.is_enabled(wm.label_key):
                    continue

                if not self.item_exists(wm.label_key, current_menu):
                    label = T.translate(wm.label_key).upper()
                    callback = self._get_change_state_callback(
                        wm.state, character=player
                    )
                    entries.append(
                        (wm.position, MenuItem(wm.label_key, label, callback))
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

        if player.items.get_items() and self.menu_flags.is_enabled("menu_bag"):
            items_filtered = ItemFilter(player)
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
                self._menu_item("menu_player", "CharacterState", kwargs=param)
            )

        if player.mission_controller.get_missions_with_met_prerequisites():
            current_menu.append(
                self._menu_item(
                    "menu_missions", "MissionState", character=player
                )
            )

        if self.menu_flags.is_enabled("menu_save"):
            current_menu.append(self._menu_item("menu_save", "SaveMenuState"))

        if self.menu_flags.is_enabled("menu_load"):
            current_menu.append(self._menu_item("menu_load", "LoadMenuState"))

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


class WorldMenuState(PygameMenuState):
    """Menu for the world state."""

    def __init__(self, menu_manager: WorldMenuManager, character: NPC) -> None:
        """Initialize menu state and build menu separately."""
        self.char = character
        super().__init__(height=prepare.SCREEN_SIZE[1])
        self.menu_manager = menu_manager
        self.menu_manager.set_menu_renderer(self)
        self.update_menu_from_manager()
        self.handler = MonsterMenuHandler(self.client, self.char)

    def update_menu_from_manager(self) -> None:
        """Refreshes the menu display using items provided by the manager."""
        display = self.menu_manager.build_current_menu_items(self.char)
        add_menu_items_to_pygame_menu(self.menu, display)

    def open_monster_menu(self) -> None:
        self.handler.open_monster_menu()

    def update_animation_position(self) -> None:
        self.menu.translate(-self.animation_offset, 0)

    def animate_open(self) -> Animation:
        width = self.menu.get_width(border=True)
        self.animation_offset = 0
        ani = self.animate(self, animation_offset=width, duration=0.50)
        ani.schedule(self.update_animation_position, ScheduleType.ON_UPDATE)
        return ani

    def animate_close(self) -> Animation:
        ani = self.animate(self, animation_offset=0, duration=0.50)
        ani.schedule(self.update_animation_position, ScheduleType.ON_UPDATE)
        return ani

    def process_event(self, event: PlayerInput) -> Optional[PlayerInput]:
        if (
            event.button in (buttons.START, buttons.B, buttons.BACK)
            and event.pressed
        ):
            self.client.pop_state()
            return None
        return super().process_event(event)
