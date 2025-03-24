# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Generator
from functools import partial
from typing import TYPE_CHECKING, Optional

import pygame

from tuxemon import prepare, tools
from tuxemon.item.item import Item
from tuxemon.locale import T
from tuxemon.menu.interface import MenuItem
from tuxemon.menu.menu import Menu
from tuxemon.menu.quantity import QuantityAndCostMenu, QuantityAndPriceMenu
from tuxemon.platform.const import buttons
from tuxemon.platform.events import PlayerInput
from tuxemon.sprite import Sprite
from tuxemon.ui.text import TextArea

if TYPE_CHECKING:
    from tuxemon.economy import Economy
    from tuxemon.npc import NPC

INFINITE_ITEMS = prepare.INFINITE_ITEMS


class ShopMenuState(Menu[Item]):
    background_filename = prepare.BG_SHOP
    draw_borders = False

    def __init__(
        self,
        buyer: NPC,
        seller: NPC,
        economy: Economy,
        buyer_purge: bool = False,
    ) -> None:
        super().__init__()

        # this sprite is used to display the item
        self.item_center = self.rect.width * 0.164, self.rect.height * 0.13
        self.item_sprite = Sprite()
        self.sprites.add(self.item_sprite)

        self.menu_items.line_spacing = tools.scale(7)
        self.current_page = 0
        self.total_pages = 0
        self.inventory: list[Item] = []

        # this is the area where the item description is displayed
        rect = self.client.screen.get_rect()
        rect.top = tools.scale(106)
        rect.left = tools.scale(3)
        rect.width = tools.scale(250)
        rect.height = tools.scale(32)
        self.text_area = TextArea(self.font, self.font_color)
        self.text_area.rect = rect
        self.sprites.add(self.text_area, layer=100)

        self.image_center = self.rect.width * 0.16, self.rect.height * 0.45
        self.buyer = buyer
        self.seller = seller
        self.buyer_purge = buyer_purge
        self.economy = economy
        self.buyer_manager = self.buyer.money_controller.money_manager
        self.seller_manager = self.seller.money_controller.money_manager

    def calc_internal_rect(self) -> pygame.rect.Rect:
        # area in the screen where the item list is
        rect = self.rect.copy()
        rect.width = int(rect.width * 0.58)
        rect.left = int(self.rect.width * 0.365)
        rect.top = int(rect.height * 0.05)
        rect.height = int(self.rect.height * 0.60)
        return rect

    def initialize_items(self) -> Generator[MenuItem[Item], None, None]:
        """Get all player inventory items and add them to menu."""
        inventory = []
        # when the player buys
        if self.buyer.isplayer:
            inventory = [item for item in self.seller.items]
        # when the player sells
        if self.seller.isplayer:
            inventory = [
                item
                for item in self.seller.items
                for t in self.economy.model.items
                if item.slug == t.name
            ]

        # required because the max() below will fail if inv empty
        if not inventory:
            return

        # when the player buys, sort based on price
        if self.buyer.isplayer:
            inventory = sorted(
                inventory, key=lambda x: self.economy.lookup_item_price(x.slug)
            )
        # when the player buys, sort based on cost
        if self.seller.isplayer:
            inventory = sorted(
                inventory, key=lambda x: self.economy.lookup_item_cost(x.slug)
            )

        self.inventory = inventory

        page_size = prepare.MAX_MENU_ITEMS
        self.total_pages = -(-len(inventory) // page_size)

        self.current_page = max(
            0, min(self.current_page, self.total_pages - 1)
        )

        start_index = self.current_page * page_size
        end_index = (self.current_page + 1) * page_size
        page_items = inventory[start_index:end_index]

        for itm in page_items:
            # buying
            if self.buyer.isplayer:
                # recall variable quantity
                key = f"{self.economy.model.slug}:{itm.slug}"
                self.qty = self.buyer.game_variables[key]

                fg = None
                self.wallet = self.buyer_manager.get_money()
                self.price = self.economy.lookup_item_price(itm.slug)
                if self.price > self.wallet:
                    fg = self.unavailable_color_shop
                if itm.quantity != INFINITE_ITEMS:
                    if self.qty == 0:
                        label = f"${self.price:4} {T.translate('shop_buy_soldout')}"
                    else:
                        label = f"${self.price:4} {itm.name} x {self.qty}"
                else:
                    label = f"${self.price:4} {itm.name}"
                image = self.shadow_text(label, fg=fg)
                yield MenuItem(image, itm.name, itm.description, itm)
            # selling
            if self.seller.isplayer:
                self.cost = self.economy.lookup_item_cost(itm.slug)
                if itm.quantity != INFINITE_ITEMS:
                    label = f"${self.cost:3} {itm.name} x {itm.quantity}"
                else:
                    label = f"${self.cost:3} {itm.name}"
                image = self.shadow_text(label)
                yield MenuItem(image, itm.name, itm.description, itm)

    def is_valid_entry(self, item: Optional[Item]) -> bool:
        if self.buyer.isplayer and item:
            if self.price > self.wallet:
                return False
            if self.qty == 0:
                return False
        return True

    def on_menu_selection_change(self) -> None:
        """Called when menu selection changes."""
        item = self.get_selected_item()
        if item:
            image = item.game_object.surface
            assert image
            self.item_sprite.image = image
            self.item_sprite.rect = image.get_rect(center=self.image_center)
            if item.description:
                self.alert(item.description)

    def get_current_page_number(self) -> int:
        """
        Returns the current page number.
        """
        return self.current_page

    def prev_page(self) -> None:
        """
        Goes to the previous page.

        This method clears the current page, decrements the current page number,
        and then adds the items from the previous page to the menu.
        """
        if self.current_page > 0:
            self.current_page -= 1
            self.reload_shop()

    def next_page(self) -> None:
        """
        Goes to the next page.

        This method clears the current page, increments the current page number,
        and then adds the items from the next page to the menu.
        """
        page_size = prepare.MAX_MENU_ITEMS
        total_pages = -(-len(self.inventory) // page_size)
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self.reload_shop()

    def reload_shop(self) -> None:
        self.clear()
        page_size = prepare.MAX_MENU_ITEMS
        start_index = self.current_page * page_size
        end_index = (self.current_page + 1) * page_size
        page_items = self.inventory[start_index:end_index]

        for itm in page_items:
            if self.buyer.isplayer:
                key = f"{self.economy.model.slug}:{itm.slug}"
                self.qty = self.buyer.game_variables[key]
                fg = None
                self.wallet = self.buyer_manager.get_money()
                self.price = self.economy.lookup_item_price(itm.slug)
                if self.price > self.wallet:
                    fg = self.unavailable_color_shop
                if itm.quantity != INFINITE_ITEMS:
                    if self.qty == 0:
                        label = f"${self.price:4} {T.translate('shop_buy_soldout')}"
                    else:
                        label = f"${self.price:4} {itm.name} x {self.qty}"
                else:
                    label = f"${self.price:4} {itm.name}"
                image = self.shadow_text(label, fg=fg)
                self.add(MenuItem(image, itm.name, itm.description, itm))
            if self.seller.isplayer:
                self.cost = self.economy.lookup_item_cost(itm.slug)
                if itm.quantity != INFINITE_ITEMS:
                    label = f"${self.cost:3} {itm.name} x {itm.quantity}"
                else:
                    label = f"${self.cost:3} {itm.name}"
                image = self.shadow_text(label)
                self.add(MenuItem(image, itm.name, itm.description, itm))

        # Adjust selected_index if it's out of bounds after reloading
        if self.menu_items:
            self.selected_index = min(
                self.selected_index, len(self.menu_items) - 1
            )
        else:
            self.selected_index = -1
        self.on_menu_selection_change()

    def process_event(self, event: PlayerInput) -> Optional[PlayerInput]:
        """
        Processes a player input event.

        Parameters:
            event: The player input event.

        Returns:
            Optional[PlayerInput]: The processed event or None if it's not handled.
        """
        if event.button == buttons.RIGHT and event.pressed:
            if self.current_page <= self.total_pages:
                self.next_page()
        elif event.button == buttons.LEFT and event.pressed:
            if self.current_page >= 0:
                self.prev_page()
        else:
            return super().process_event(event)
        return None


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
        price = self.economy.lookup_item_price(item.slug)
        label = f"{self.economy.model.slug}:{item.slug}"

        def buy_item(itm: Item, quantity: int) -> None:
            if not quantity:
                return

            in_bag = self.buyer.find_item(itm.slug)
            if in_bag:
                # reduces quantity only no-infinite items
                if itm.quantity != INFINITE_ITEMS:
                    itm.quantity -= quantity
                    self.buyer.game_variables[label] -= quantity
                in_bag.quantity += quantity
            else:
                if itm.quantity != INFINITE_ITEMS:
                    itm.quantity -= quantity
                    self.buyer.game_variables[label] -= quantity
                new_buy = Item()
                new_buy.load(itm.slug)
                new_buy.quantity = quantity
                self.buyer.add_item(new_buy)
            amount = quantity * price
            self.buyer_manager.remove_money(amount)

            self.reload_items()
            if item not in self.seller.items:
                # We're pointing at a new item
                self.on_menu_selection_change()

        money = self.buyer_manager.get_money()
        qty_can_afford = int(money / price)
        inventory = self.buyer.game_variables[label]
        _inventory = 99999 if inventory == INFINITE_ITEMS else inventory
        max_quantity = min(_inventory, qty_can_afford)

        self.client.push_state(
            QuantityAndPriceMenu(
                callback=partial(buy_item, item),
                max_quantity=max_quantity,
                quantity=1,
                shrink_to_items=True,
                price=price,
            )
        )


class ShopSellMenuState(ShopMenuState):
    """This is the state for when a player wants to buy something."""

    def on_menu_selection(self, menu_item: MenuItem[Item]) -> None:
        """
        Called when player has selected something from the inventory.

        Currently, opens a new menu depending on the state context.

        Parameters:
            menu_item: Selected menu item.

        """
        item = menu_item.game_object
        cost = self.economy.lookup_item_cost(item.slug)

        def sell_item(itm: Item, quantity: int) -> None:
            if not quantity:
                return

            diff = itm.quantity - quantity
            if diff <= 0:
                self.seller.remove_item(itm)
            else:
                itm.quantity = diff

            amount = quantity * cost
            self.seller_manager.add_money(amount)

            self.reload_items()
            if item not in self.seller.items:
                # We're pointing at a new item
                self.on_menu_selection_change()

        self.client.push_state(
            QuantityAndCostMenu(
                callback=partial(sell_item, item),
                max_quantity=item.quantity,
                quantity=1,
                shrink_to_items=True,
                cost=cost,
            )
        )
