# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import math
from collections.abc import Callable, Generator
from typing import TYPE_CHECKING, Any, ClassVar

from pygame.rect import Rect

from tuxemon.graphics import load_and_scale
from tuxemon.item.controller import ItemController
from tuxemon.item.filter import ItemFilter
from tuxemon.item.item import Item
from tuxemon.item.sorter import ItemSorter
from tuxemon.locale.locale import T
from tuxemon.menu.interface import MenuItem
from tuxemon.menu.menu import Menu
from tuxemon.platform.const import buttons
from tuxemon.platform.const.graphics import (
    BG_ITEMS,
    BG_ITEMS_BACKPACK,
    DIMGRAY_COLOR,
    MISSING_IMAGE,
)
from tuxemon.platform.const.sizes import MAX_MENU_ITEMS
from tuxemon.platform.events import PlayerInput
from tuxemon.session import local_session
from tuxemon.sprite import Sprite
from tuxemon.tools import open_choice_dialog, open_dialog
from tuxemon.ui.text import TextArea

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient
    from tuxemon.entity.npc import NPC


class ItemMenuState(Menu[Item]):
    """The item menu allows you to view and use items in your inventory."""

    name: ClassVar[str] = "ItemMenuState"
    background_filename = BG_ITEMS
    draw_borders = False

    def __init__(
        self,
        client: BaseClient,
        character: NPC,
        source: str,
        item_filter: ItemFilter | None = None,
        sorter: ItemSorter | None = None,
        on_selection: Callable[[MenuItem[Item]], None] | None = None,
        is_valid_entry: Callable[[Item | None], bool] | None = None,
        **kwargs: Any,
    ) -> None:
        self.char = character
        self.source = source
        super().__init__(client=client, **kwargs)

        self.filter_controller = item_filter or ItemFilter(self.char.items)
        self.sorter = sorter or ItemSorter()
        self._external_on_selection = on_selection
        self._external_is_valid_entry = is_valid_entry
        # this sprite is used to display the item
        # it's also animated to pop out of the backpack
        self.item_center = self.rect.width * 0.164, self.rect.height * 0.13
        self.item_sprite = Sprite()
        self.sprites.add(self.item_sprite)

        self.menu_items.line_spacing = self.client.context.scaling.scale_int(7)
        self.current_page = 0
        self.total_pages = 0
        self.inventory = self.filter_controller.get_filtered_inventory()
        self._cursor_positioned = False

        # this is the area where the item description is displayed
        rect = self.client.context.rect.copy()
        rect.top = self.client.context.scaling.scale_int(106)
        rect.left = self.client.context.scaling.scale_int(3)
        rect.width = self.client.context.scaling.scale_int(250)
        rect.height = self.client.context.scaling.scale_int(32)
        self.text_area = TextArea(
            font=self.font,
            font_color=self.font_color,
            rect=rect,
            scaling=self.client.context.scaling,
            font_shadow=(96, 96, 128),
        )
        self.sprites.add(self.text_area, layer=100)
        self.page_number_display = TextArea(
            font=self.font,
            font_color=self.font_color,
            rect=Rect(0, 0, 1, 1),
            scaling=self.client.context.scaling,
        )
        self.sprites.add(self.page_number_display, layer=100)
        self.page_size = MAX_MENU_ITEMS

        # load the backpack icon
        self.backpack_center = self.rect.width * 0.16, self.rect.height * 0.45
        self.load_sprite(
            BG_ITEMS_BACKPACK,
            center=self.backpack_center,
            layer=100,
        )

    def calc_internal_rect(self) -> Rect:
        # area in the screen where the item list is
        rect = self.rect.copy()
        rect.width = int(rect.width * 0.58)
        rect.left = int(self.rect.width * 0.365)
        rect.top = int(rect.height * 0.05)
        rect.height = int(self.rect.height * 0.60)
        return rect

    def on_menu_selection(self, menu_item: MenuItem[Item]) -> None:
        """
        Called when player has selected something from the inventory.
        """
        if self._external_on_selection:
            return self._external_on_selection(menu_item)

        item = menu_item.game_object

        # Check if the item can be used on any monster
        if not any(
            item.validate_monster(local_session, m) for m in self.char.monsters
        ):
            self.on_menu_selection_change()
            error_message = self.get_error_message(item)
            open_dialog(self.client, [error_message])
            return

        # Check if the item can be used in the current state
        if not any(
            s.name in self.client.active_state_names for s in item.usable_in
        ):
            error_message = T.format(
                "item_cannot_use_here", {"name": item.name}
            )
            open_dialog(self.client, [error_message])
            return

        # All checks passed, proceed to confirmation
        self.open_confirm_use_menu(item)

    def open_confirm_use_menu(self, item: Item) -> None:
        """
        Opens a confirmation menu for the given item, dynamically creating options.
        """
        controller = ItemController(local_session, item, self.char)
        menu_options = controller.get_confirm_menu_options()
        open_choice_dialog(self.client, menu_options, escape_key_exits=True)

    def get_error_message(self, item: Item) -> str:
        """
        Returns an error message based on the item's conditions.

        Parameters:
            item: The item to check.

        Returns:
            An error message.
        """
        for condition in item.conditions:
            if condition.name == "location_inside":
                loc_inside = getattr(condition, "location_inside")
                return T.format(
                    "item_used_wrong_location_inside",
                    {
                        "name": item.name.upper(),
                        "here": T.translate(loc_inside),
                    },
                )
            elif condition.name == "location_type":
                loc_type = getattr(condition, "location_type")
                return T.format(
                    "item_used_wrong_location_type",
                    {
                        "name": item.name.upper(),
                        "here": T.translate(loc_type),
                    },
                )
            elif condition.name in ["facing_tile", "facing_sprite"]:
                return T.format("item_cannot_use_here", {"name": item.name})
        return T.format("item_no_available_target", {"name": item.name})

    def initialize_items(self) -> Generator[MenuItem[Item], None, None]:
        """Get all player inventory items and add them to menu."""
        self.inventory = self.filter_controller.get_filtered_inventory()

        if not self.inventory:
            self.total_pages = 1
            self.current_page = 0
            return

        # Compute total pages using VisualSpriteList pagination
        if self.page_size:
            self.total_pages = max(
                1, math.ceil(len(self.inventory) / self.page_size)
            )
        else:
            self.total_pages = 1

        # Clamp current page
        self.current_page = max(
            0, min(self.current_page, self.total_pages - 1)
        )

        # Slice items for this page
        start = self.current_page * self.page_size
        end = start + self.page_size
        page_items = self.inventory[start:end]

        for obj in self.sorter.sort(page_items):
            enable = self.is_valid_entry(obj)
            menu_item = self.create_menu_item(obj, is_enabled=enable)
            yield menu_item

    def on_menu_selection_change(self) -> None:
        """Called when menu selection changes."""
        selected_item = self.get_selected_item()
        if selected_item:
            self.animate_item_selection(selected_item.game_object)
            self.show_item_description(selected_item.game_object)

    def is_valid_entry(self, item: Item | None) -> bool:
        if self._external_is_valid_entry:
            return self._external_is_valid_entry(item)
        return item is not None

    def animate_item_selection(self, item: Item) -> None:
        """Animate the selected item being pulled from the bag."""
        image = item.surface
        if not image:
            image = load_and_scale(MISSING_IMAGE)

        self.item_sprite.image = image
        self.item_sprite.rect = image.get_rect(center=self.backpack_center)
        self.animate(
            self.item_sprite.rect,
            centery=self.item_center[1],
            duration=0.2,
        )

    def show_item_description(self, item: Item) -> None:
        """Show the description of the selected item."""
        if item.description:
            self.dialog.alert(
                item.description, self.text_area, dialog_speed="max"
            )

    def reload_items(self) -> None:
        self.clear()
        self.inventory = self.filter_controller.get_filtered_inventory()

        # Recompute total pages
        if self.page_size:
            self.total_pages = max(
                1, math.ceil(len(self.inventory) / self.page_size)
            )
        else:
            self.total_pages = 1

        # On the first open, seek the page that holds the last-used item.
        seek_slug: str | None = None
        if not self._cursor_positioned:
            if self.source == "MainCombatMenuState":
                seek_slug = self.char.battle_last_used_item_slug
            else:
                seek_slug = self.char.last_used_item_slug
            if seek_slug and self.page_size:
                inv_slugs = [item.slug for item in self.inventory]
                if seek_slug in inv_slugs:
                    item_global_index = inv_slugs.index(seek_slug)
                    self.current_page = item_global_index // self.page_size

        # Clamp current page
        self.current_page = max(
            0, min(self.current_page, self.total_pages - 1)
        )

        # Slice items for this page
        start = self.current_page * self.page_size
        end = start + self.page_size
        page_items = self.inventory[start:end]

        if not page_items:
            self.selected_index = -1
            self.total_pages = 1
            self.current_page = 0
            self.update_page_number_display(0)
            self._cursor_positioned = True
            return

        sorted_items = self.sorter.sort(page_items)

        for obj in sorted_items:
            enable = self.is_valid_entry(obj)
            menu_item = self.create_menu_item(obj, is_enabled=enable)
            self.add(menu_item)

        if self.menu_items:
            if seek_slug:
                target_index = next(
                    (
                        i
                        for i, obj in enumerate(sorted_items)
                        if obj.slug == seek_slug
                    ),
                    None,
                )
                self.selected_index = (
                    target_index
                    if target_index is not None
                    else min(self.selected_index, len(self.menu_items) - 1)
                )
            else:
                self.selected_index = min(
                    self.selected_index, len(self.menu_items) - 1
                )
        else:
            self.selected_index = -1

        self._cursor_positioned = True
        self.update_page_number_display(len(self.inventory))
        self.on_menu_selection_change()

    def process_event(self, event: PlayerInput) -> PlayerInput | None:
        """
        Processes a player input event.

        Parameters:
            event: The player input event.

        Returns:
            Optional[PlayerInput]: The processed event or None if it's not handled.
        """
        total_pages = self.total_pages
        if event.button == buttons.RIGHT and event.pressed:
            # Move to the next page if possible
            if self.current_page < total_pages - 1:
                self.current_page += 1
                self.reload_items()
        elif event.button == buttons.LEFT and event.pressed:
            # Move to the previous page if possible
            if self.current_page > 0:
                self.current_page -= 1
                self.reload_items()
        else:
            return super().process_event(event)
        return None

    def update_page_number_display(self, total_items: int) -> None:
        internal_rect = self.calc_internal_rect()
        page_text = f"{self.current_page + 1}/{self.total_pages}"
        image = self.shadow_text(page_text)
        self.page_number_display.image = image
        self.page_number_display.rect.bottomright = internal_rect.bottomright

    def create_menu_item(
        self,
        item: Item,
        is_enabled: bool = True,
        show_quantity: bool = True,
        prefix: str = "",
    ) -> MenuItem[Item]:
        name = f"{prefix}{item.name}"
        label = f"{name} x {item.quantity}" if show_quantity else name
        image = self.shadow_text(label, bg=DIMGRAY_COLOR)
        return MenuItem(
            image=image,
            label=name,
            description=item.description,
            game_object=item,
            enabled=is_enabled,
        )
