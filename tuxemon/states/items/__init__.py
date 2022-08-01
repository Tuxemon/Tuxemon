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
# Leif Theden <leif.theden@gmail.com>
# Carlos Ramos <vnmabus@gmail.com>
#
#
# states.ItemMenuState The item menu allows you to view and use items in your inventory.
# states.ShopMenuState
#
from __future__ import annotations

from typing import Any, Generator, Iterable, Sequence, Tuple

import pygame

from tuxemon import tools
from tuxemon.item.item import InventoryItem, Item
from tuxemon.locale import T
from tuxemon.menu.interface import MenuItem
from tuxemon.menu.menu import Menu
from tuxemon.menu.quantity import QuantityAndPriceMenu, QuantityMenu
from tuxemon.monster import Monster
from tuxemon.session import local_session
from tuxemon.sprite import Sprite
from tuxemon.states.monster import MonsterMenuState
from tuxemon.ui.text import TextArea

# The import is required for PushState to work.
# But linters may say the import is unused.
assert QuantityMenu
assert QuantityAndPriceMenu


def sort_inventory(
    inventory: Iterable[InventoryItem],
) -> Sequence[InventoryItem]:
    """
    Sort inventory in a usable way. Expects a iterable of inventory properties.

    * Group items by category
    * Sort in groups by name
    * Group order: Potions, Food, Utility Items, Quest/Game Items

    Parameters:
        inventory: NPC inventory values.

    Returns:
        Sorted copy of the inventory.

    """

    def rank_item(properties: InventoryItem) -> Tuple[int, str]:
        item = properties["item"]
        primary_order = sort_order.index(item.sort)
        return primary_order, item.name

    # the two reversals are used to let name sort desc, but class sort asc
    sort_order = ["potion", "food", "utility", "quest"]
    sort_order.reverse()
    return sorted(inventory, key=rank_item, reverse=True)


class ItemMenuState(Menu[Item]):
    """The item menu allows you to view and use items in your inventory."""

    background_filename = "gfx/ui/item/item_menu_bg.png"
    draw_borders = False

    def startup(self, **kwargs: Any) -> None:
        self.state = "normal"

        # this sprite is used to display the item
        # its also animated to pop out of the backpack
        self.item_center = self.rect.width * 0.164, self.rect.height * 0.13
        self.item_sprite = Sprite()
        self.sprites.add(self.item_sprite)

        # do not move this line
        super().startup(**kwargs)
        self.menu_items.line_spacing = tools.scale(7)

        # this is the area where the item description is displayed
        rect = self.client.screen.get_rect()
        rect.top = tools.scale(106)
        rect.left = tools.scale(3)
        rect.width = tools.scale(250)
        rect.height = tools.scale(32)
        self.text_area = TextArea(self.font, self.font_color, (96, 96, 128))
        self.text_area.rect = rect
        self.sprites.add(self.text_area, layer=100)

        # load the backpack icon
        self.backpack_center = self.rect.width * 0.16, self.rect.height * 0.45
        self.load_sprite(
            "gfx/ui/item/backpack.png",
            center=self.backpack_center,
            layer=100,
        )

    def calc_internal_rect(self) -> pygame.rect.Rect:
        # area in the screen where the item list is
        rect = self.rect.copy()
        rect.width = int(rect.width * 0.58)
        rect.left = int(self.rect.width * 0.365)
        rect.top = int(rect.height * 0.05)
        rect.height = int(self.rect.height * 0.60)
        return rect

    def determine_state_called_from(self) -> str:
        dex = self.client.active_states.index(self)
        return self.client.active_states[dex + 1].name

    def on_menu_selection(self, menu_item: MenuItem[Item]) -> None:
        """
        Called when player has selected something from the inventory.

        Currently, opens a new menu depending on the state context.

        Parameters:
            menu_item: Selected menu item.

        """
        item = menu_item.game_object
        state = self.determine_state_called_from()

        if not any(
            menu_item.game_object.validate(m)
            for m in local_session.player.monsters
        ):
            msg = T.format("item_no_available_target", {"name": item.name})
            tools.open_dialog(local_session, [msg])
        elif state not in item.usable_in:
            msg = T.format("item_cannot_use_here", {"name": item.name})
            tools.open_dialog(local_session, [msg])
        else:
            self.open_confirm_use_menu(item)

    def open_confirm_use_menu(self, item: Item) -> None:
        """
        Confirm if player wants to use this item, or not.

        Parameters:
            item: Selected item.

        """

        def use_item(menu_item: MenuItem[Monster]) -> None:
            player = local_session.player
            monster = menu_item.game_object

            # item must be used before state is popped.
            result = item.use(player, monster)
            self.client.pop_state()  # pop the monster screen
            self.client.pop_state()  # pop the item screen
            tools.show_item_result_as_dialog(local_session, item, result)

        def confirm() -> None:
            self.client.pop_state()  # close the confirm dialog
            # TODO: allow items to be used on player or "in general"

            menu = self.client.push_state(MonsterMenuState)
            menu.is_valid_entry = item.validate
            menu.on_menu_selection = use_item

        def cancel() -> None:
            self.client.pop_state()  # close the use/cancel menu

        def open_choice_menu() -> None:
            # open the menu for use/cancel
            menu = self.client.push_state(Menu)
            menu.shrink_to_items = True

            menu_items_map = (
                ("item_confirm_use", confirm),
                ("item_confirm_cancel", cancel),
            )

            # add our options to the menu
            for key, callback in menu_items_map:
                label = T.translate(key).upper()
                image = self.shadow_text(label)
                item = MenuItem(image, label, None, callback)
                menu.add(item)

        open_choice_menu()

    def initialize_items(self) -> Generator[MenuItem[Item], None, None]:
        """Get all player inventory items and add them to menu."""
        inventory = local_session.player.inventory.values()

        # required because the max() below will fail if inv empty
        if not inventory:
            return

        name_len = 17  # TODO: dynamically get this value, maybe?
        count_len = max(len(str(p["quantity"])) for p in inventory)

        # TODO: move this and other format strings to a locale or config file
        label_format = "{:<{name_len}} x {:>{count_len}}".format

        for properties in sort_inventory(inventory):
            obj = properties["item"]
            formatted_name = label_format(
                obj.name,
                properties["quantity"],
                name_len=name_len,
                count_len=count_len,
            )
            image = self.shadow_text(formatted_name, bg=(128, 128, 128))
            yield MenuItem(image, obj.name, obj.description, obj)

    def on_menu_selection_change(self) -> None:
        """Called when menu selection changes."""
        item = self.get_selected_item()
        if item:
            # animate item being pulled from the bag
            image = item.game_object.surface
            self.item_sprite.image = image
            self.item_sprite.rect = image.get_rect(center=self.backpack_center)
            self.animate(
                self.item_sprite.rect,
                centery=self.item_center[1],
                duration=0.2,
            )

            # show item description
            self.alert(item.description)


class ShopMenuState(Menu[Item]):
    background_filename = "gfx/ui/item/item_menu_bg.png"
    draw_borders = False

    def startup(self, **kwargs: Any) -> None:
        self.state = "normal"

        # this sprite is used to display the item
        self.item_center = self.rect.width * 0.164, self.rect.height * 0.13
        self.item_sprite = Sprite()
        self.sprites.add(self.item_sprite)

        # do not move this line
        super().startup(**kwargs)
        self.menu_items.line_spacing = tools.scale(7)

        # this is the area where the item description is displayed
        rect = self.client.screen.get_rect()
        rect.top = tools.scale(106)
        rect.left = tools.scale(3)
        rect.width = tools.scale(250)
        rect.height = tools.scale(32)
        self.text_area = TextArea(self.font, self.font_color, (96, 96, 128))
        self.text_area.rect = rect
        self.sprites.add(self.text_area, layer=100)

        self.image_center = self.rect.width * 0.16, self.rect.height * 0.45
        self.buyer = kwargs["buyer"]
        self.seller = kwargs["seller"]
        self.buyer_purge = kwargs.get("buyer_purge", False)
        self.economy = kwargs["economy"]

    def calc_internal_rect(self) -> pygame.rect.Rect:
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

        Currently, opens a new menu depending on the state context.

        Parameters:
            menu_item: Selected menu item.

        """
        item = menu_item.game_object

        def use_item(quantity: int) -> None:
            if not quantity:
                return

            if self.buyer:
                self.seller.give_item(self.client, self.buyer, item, quantity)
            else:
                self.seller.alter_item_quantity(
                    self.client,
                    item.slug,
                    -quantity,
                )
            self.reload_items()
            if not self.seller.has_item(item.slug):
                # We're pointing at a new item
                self.on_menu_selection_change()

        item_dict = self.seller.inventory[item.slug]
        max_quantity = (
            None if item_dict.get("infinite") else item_dict["quantity"]
        )

        self.client.push_state(
            QuantityMenu,
            callback=use_item,
            max_quantity=max_quantity,
            quantity=1,
            shrink_to_items=True,
        )

    def initialize_items(self) -> Generator[MenuItem[Item], None, None]:
        """Get all player inventory items and add them to menu."""
        inventory = [
            item
            for item in self.seller.inventory.values()
            if not (self.seller.isplayer and item["item"].sort == "quest")
        ]

        # required because the max() below will fail if inv empty
        if not inventory:
            return

        name_len = 17  # TODO: dynamically get this value, maybe?
        count_len = max(len(str(p["quantity"])) for p in inventory)

        # TODO: move this and other format strings to a locale or config file
        label_format_1 = "{:<{name_len}} x {:>{count_len}}".format
        label_format_2 = "{:<{name_len}}".format

        for properties in sort_inventory(inventory):
            obj = properties["item"]
            if properties.get("infinite"):
                label = label_format_2
            else:
                label = label_format_1
            formatted_name = label(
                obj.name,
                properties["quantity"],
                name_len=name_len,
                count_len=count_len,
            )
            image = self.shadow_text(formatted_name, bg=(128, 128, 128))
            yield MenuItem(image, obj.name, obj.description, obj)

    def on_menu_selection_change(self) -> None:
        """Called when menu selection changes."""
        item = self.get_selected_item()
        if item:
            image = item.game_object.surface
            self.item_sprite.image = image
            self.item_sprite.rect = image.get_rect(center=self.image_center)
            self.alert(item.description)


class ShopBuyMenuState(ShopMenuState):
    """This is the state for when a player wants to buy something."""

    def on_menu_selection(self, menu_item: MenuItem[Item]) -> None:
        """
        Called when player has selected something from the shop's inventory.

        Currently, opens a new menu depending on the state context.

        Parameters:
            menu_item: Selected menu item.

        """
        item = menu_item.game_object

        def buy_item(quantity: int) -> None:
            if not quantity:
                return

            self.buyer.buy_transaction(
                self.client, self.seller, item.slug, quantity, price
            )

            self.reload_items()
            if not self.seller.has_item(item.slug):
                # We're pointing at a new item
                self.on_menu_selection_change()

        item_dict = self.seller.inventory[item.slug]

        price = (
            1
            if not self.economy
            or not self.economy.lookup_item_price(item.slug)
            else self.economy.lookup_item_price(item.slug)
        )
        money = self.buyer.game_variables.get("money")
        qty_buyer_can_afford = int(money / price) if money else 0
        max_quantity = (
            qty_buyer_can_afford
            if item_dict.get("infinite")
            else min(item_dict["quantity"], qty_buyer_can_afford)
        )

        self.client.push_state(
            QuantityAndPriceMenu,
            callback=buy_item,
            max_quantity=max_quantity,
            quantity=0 if max_quantity == 0 else 1,
            shrink_to_items=True,
            price=price,
        )
