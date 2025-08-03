# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Generator, Sequence
from typing import TYPE_CHECKING, Optional

from pygame.rect import Rect

from tuxemon import prepare
from tuxemon.item.controller import ItemController
from tuxemon.item.filter import ItemFilter
from tuxemon.item.item import Item
from tuxemon.item.sorter import ItemSorter
from tuxemon.locale import T
from tuxemon.menu.interface import MenuItem
from tuxemon.menu.menu import Menu
from tuxemon.platform.const import buttons
from tuxemon.platform.events import PlayerInput
from tuxemon.session import local_session
from tuxemon.sprite import Sprite
from tuxemon.tools import (
    open_choice_dialog,
    open_dialog,
    scale,
)
from tuxemon.ui.paginator import Paginator
from tuxemon.ui.text import TextArea

if TYPE_CHECKING:
    from tuxemon.npc import NPC


def sort_inventory(
    inventory: Sequence[Item], sort_order: Optional[list[str]] = None
) -> Sequence[Item]:
    """
    Sorts a given inventory of items by category and name for improved usability.

    The function performs the following steps:
    - Groups items by their category as defined by the `sort` attribute of each item.
    - Sorts items within each category alphabetically by name.
    - Orders categories according to `sort_order` if provided, otherwise defaults to:
      ["potion", "food", "utility", "quest"].
    - Items with unrecognized categories are placed after known categories, sorted by name.

    Parameters:
        inventory: A sequence of inventory items, where each item has
            a `name` and `sort` attribute.
        sort_order: A list specifying the desired order of item categories.
            If not provided, defaults to ["potion", "food", "utility", "quest"].

    Returns:
        A new sequence of inventory items sorted by category and name.
    """
    default_order = ["potion", "food", "utility", "quest"]
    order_list = sort_order or default_order
    sort_order_rank = {
        category: index for index, category in enumerate(order_list)
    }

    def rank_item(item: Item) -> tuple[int, str]:
        # Unknown types last
        rank = sort_order_rank.get(item.sort, len(order_list))
        return rank, item.name

    return sorted(inventory, key=rank_item)


class ItemMenuState(Menu[Item]):
    """The item menu allows you to view and use items in your inventory."""

    background_filename = prepare.BG_ITEMS
    draw_borders = False

    def __init__(
        self,
        character: NPC,
        source: str,
        item_filter: Optional[ItemFilter] = None,
        sorter: Optional[ItemSorter] = None,
    ) -> None:
        self.char = character
        self.source = source
        super().__init__()

        self.filter_controller = item_filter or ItemFilter(character)
        self.sorter = sorter or ItemSorter()
        # this sprite is used to display the item
        # it's also animated to pop out of the backpack
        self.item_center = self.rect.width * 0.164, self.rect.height * 0.13
        self.item_sprite = Sprite()
        self.sprites.add(self.item_sprite)

        self.menu_items.line_spacing = scale(7)
        self.current_page = 0
        self.total_pages = 0
        self.inventory = self.filter_controller.get_filtered_inventory()

        # this is the area where the item description is displayed
        rect = self.client.screen.get_rect()
        rect.top = scale(106)
        rect.left = scale(3)
        rect.width = scale(250)
        rect.height = scale(32)
        self.text_area = TextArea(self.font, self.font_color, (96, 96, 128))
        self.text_area.rect = rect
        self.sprites.add(self.text_area, layer=100)
        self.page_number_display = TextArea(self.font, self.font_color)
        self.sprites.add(self.page_number_display, layer=100)
        self.page_size = prepare.MAX_MENU_ITEMS

        # load the backpack icon
        self.backpack_center = self.rect.width * 0.16, self.rect.height * 0.45
        self.load_sprite(
            prepare.BG_ITEMS_BACKPACK,
            center=self.backpack_center,
            layer=100,
        )
        self.paginator = Paginator(self.inventory, self.page_size)

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
        item = menu_item.game_object

        # Check if the item can be used on any monster
        if not any(
            item.validate_monster(local_session, m) for m in self.char.monsters
        ):
            self.on_menu_selection_change()
            error_message = self.get_error_message(item)
            open_dialog(self.client, [error_message])
        # Check if the item can be used in the current state
        elif not any(
            s.name in self.client.active_state_names for s in item.usable_in
        ):
            error_message = T.format(
                "item_cannot_use_here", {"name": item.name}
            )
            open_dialog(self.client, [error_message])
        else:
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

        self.total_pages = self.paginator.total_pages()

        self.current_page = max(
            0, min(self.current_page, self.total_pages - 1)
        )

        start_index = self.current_page * self.page_size
        end_index = (self.current_page + 1) * self.page_size
        page_items = self.inventory[start_index:end_index]

        for obj in sort_inventory(page_items):
            enable = self.is_valid_entry(obj)
            menu_item = self.create_menu_item(obj, is_enabled=enable)
            yield menu_item

    def on_menu_selection_change(self) -> None:
        """Called when menu selection changes."""
        selected_item = self.get_selected_item()
        if selected_item:
            self.animate_item_selection(selected_item.game_object)
            self.show_item_description(selected_item.game_object)

    def is_valid_entry(self, item: Optional[Item]) -> bool:
        return item is not None

    def animate_item_selection(self, item: Item) -> None:
        """Animate the selected item being pulled from the bag."""
        image = item.surface
        assert image
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
            self.alert(item.description)

    def reload_items(self) -> None:
        self.clear()
        self.inventory = self.filter_controller.get_filtered_inventory()

        total_pages, page_items = self.paginator.calculate_page_data(
            self.current_page
        )

        if not page_items:
            self.selected_index = -1
            self.total_pages = 1
            self.current_page = 0
            self.update_page_number_display(0)
            return

        for obj in sort_inventory(page_items):
            enable = self.is_valid_entry(obj)
            menu_item = self.create_menu_item(obj, is_enabled=enable)
            self.add(menu_item)

        if self.menu_items:
            self.selected_index = min(
                self.selected_index, len(self.menu_items) - 1
            )
        else:
            self.selected_index = -1

        self.update_page_number_display(len(self.inventory))
        self.on_menu_selection_change()

    def process_event(self, event: PlayerInput) -> Optional[PlayerInput]:
        """
        Processes a player input event.

        Parameters:
            event: The player input event.

        Returns:
            Optional[PlayerInput]: The processed event or None if it's not handled.
        """
        total_pages = self.paginator.total_pages()
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
        total_pages, _ = self.paginator.calculate_page_data(self.current_page)
        page_text = f"{self.current_page + 1}/{total_pages}"
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
        image = self.shadow_text(label, bg=prepare.DIMGRAY_COLOR)
        return MenuItem(
            image=image,
            label=name,
            description=item.description,
            game_object=item,
            enabled=is_enabled,
        )
