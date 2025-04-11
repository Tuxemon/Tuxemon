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
from tuxemon.ui.paginator import Paginator
from tuxemon.ui.text import TextArea

if TYPE_CHECKING:
    from tuxemon.economy import Economy
    from tuxemon.money import MoneyManager
    from tuxemon.npc import NPC

INFINITE_ITEMS = prepare.INFINITE_ITEMS


class ShopMenuState(Menu[Item]):
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
        self.update_background(self.economy.model.background)
        self.buyer_manager = self.buyer.money_controller.money_manager
        self.seller_manager = self.seller.money_controller.money_manager
        self.transaction_manager = TransactionManager(
            self.economy, self.buyer_manager, self.seller_manager
        )

    def calc_internal_rect(self) -> pygame.rect.Rect:
        # area in the screen where the item list is
        rect = self.rect.copy()
        rect.width = int(rect.width * 0.58)
        rect.left = int(self.rect.width * 0.365)
        rect.top = int(rect.height * 0.05)
        rect.height = int(self.rect.height * 0.60)
        return rect

    def is_valid_entry(self, item: Optional[Item]) -> bool:
        """Check if the selected item is valid for purchase or sale."""
        if not item:
            return False
        if self.buyer.isplayer:
            price = self.economy.lookup_item_price(item.slug)
            wallet = self.buyer_manager.get_money()
            key = f"{self.economy.model.slug}:{item.slug}"
            qty = self.buyer.game_variables.get(key, 0)
            if price > wallet or qty == 0:
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

    def get_filtered_inventory(self) -> list[Item]:
        """Filter and sort the inventory to exclude sold-out items."""
        return filter_inventory(
            self.buyer, self.seller, self.economy, self.buyer.isplayer
        )

    def generate_item_label(
        self,
        item: Item,
        qty: Optional[int] = None,
        price: Optional[int] = None,
        seller_mode: bool = False,
    ) -> str:
        """Generate the label for shop items, handling both buyer and seller modes."""
        return generate_item_label(item, self.economy, qty, price, seller_mode)

    def _populate_menu_items(
        self, inventory: list[Item]
    ) -> Generator[MenuItem[Item], None, None]:
        for item in inventory:
            if self.buyer.isplayer:
                key = f"{self.economy.model.slug}:{item.slug}"
                qty = self.buyer.game_variables.get(key, 0)
                price = self.economy.lookup_item_price(item.slug)
                fg = (
                    self.unavailable_color_shop
                    if price > self.buyer_manager.get_money()
                    else None
                )
                label = self.generate_item_label(item, qty, price)
                image = self.shadow_text(label, fg=fg)
                menu_item = MenuItem(image, item.name, item.description, item)
                yield menu_item
                if hasattr(self, "add"):
                    self.add(menu_item)
            elif self.seller.isplayer:
                cost = self.economy.lookup_item(item.slug, "cost") or round(
                    item.cost * self.economy.model.resale_multiplier
                )
                label = self.generate_item_label(
                    item, qty=None, price=cost, seller_mode=True
                )
                image = self.shadow_text(label)
                menu_item = MenuItem(image, item.name, item.description, item)
                yield menu_item
                if hasattr(self, "add"):
                    self.add(menu_item)

    def initialize_items(self) -> Generator[MenuItem[Item], None, None]:
        self.inventory = self.get_filtered_inventory()
        if not self.inventory:
            return

        page_size = prepare.MAX_MENU_ITEMS
        self.total_pages = Paginator.total_pages(self.inventory, page_size)
        self.current_page = max(
            0, min(self.current_page, self.total_pages - 1)
        )

        paged_inventory = Paginator.paginate(
            self.inventory, page_size, self.current_page
        )
        yield from self._populate_menu_items(paged_inventory)

    def reload_shop(self) -> None:
        self.clear()
        self.inventory = self.get_filtered_inventory()

        page_size = prepare.MAX_MENU_ITEMS
        paged_inventory = Paginator.paginate(
            self.inventory, page_size, self.current_page
        )
        list(
            self._populate_menu_items(paged_inventory)
        )  # Force generator execution

        self.selected_index = (
            min(self.selected_index, len(self.menu_items) - 1)
            if self.menu_items
            else -1
        )
        self.on_menu_selection_change()

    def process_event(self, event: PlayerInput) -> Optional[PlayerInput]:
        page_size = prepare.MAX_MENU_ITEMS
        total_pages = Paginator.total_pages(self.inventory, page_size)

        if event.button == buttons.RIGHT and event.pressed:
            # Move to the next page if possible
            if self.current_page < total_pages - 1:
                self.current_page += 1
                self.reload_shop()
        elif event.button == buttons.LEFT and event.pressed:
            # Move to the previous page if possible
            if self.current_page > 0:
                self.current_page -= 1
                self.reload_shop()
        else:
            return super().process_event(event)

        return None


class ShopBuyMenuState(ShopMenuState):
    """State for buying items."""

    def on_menu_selection(self, menu_item: MenuItem[Item]) -> None:
        item = menu_item.game_object
        price = self.economy.lookup_item_price(item.slug)
        label = f"{self.economy.model.slug}:{item.slug}"

        def buy_item(quantity: int) -> None:
            self.transaction_manager.buy_item(
                self.buyer, item, quantity, label
            )
            self.reload_items()
            if item not in self.seller.items:
                self.on_menu_selection_change()

        money = self.buyer_manager.get_money()
        qty_can_afford = int(money / price)
        inventory = self.buyer.game_variables.get(label, INFINITE_ITEMS)
        max_quantity = min(
            qty_can_afford, inventory if inventory != INFINITE_ITEMS else 99999
        )

        self.client.push_state(
            QuantityAndPriceMenu(
                callback=partial(buy_item),
                max_quantity=max_quantity,
                quantity=1,
                shrink_to_items=True,
                price=price,
            )
        )


class ShopSellMenuState(ShopMenuState):
    """State for selling items."""

    def on_menu_selection(self, menu_item: MenuItem[Item]) -> None:
        item = menu_item.game_object
        cost = self.economy.lookup_item(item.slug, "cost") or round(
            item.cost * self.economy.model.resale_multiplier
        )

        def sell_item(quantity: int) -> None:
            self.transaction_manager.sell_item(self.seller, item, quantity)
            self.reload_items()
            if item not in self.seller.items:
                self.on_menu_selection_change()

        self.client.push_state(
            QuantityAndCostMenu(
                callback=partial(sell_item),
                max_quantity=item.quantity,
                quantity=1,
                shrink_to_items=True,
                cost=cost,
            )
        )


class TransactionManager:
    """Handles all transaction operations for the shop."""

    def __init__(
        self,
        economy: Economy,
        buyer_manager: MoneyManager,
        seller_manager: MoneyManager,
    ) -> None:
        self.economy = economy
        self.buyer_manager = buyer_manager
        self.seller_manager = seller_manager

    def buy_item(
        self, buyer: NPC, item: Item, quantity: int, label: str
    ) -> None:
        """Process buying of items."""
        if item.quantity != INFINITE_ITEMS:
            item.quantity -= quantity
            buyer.game_variables[label] -= quantity

        in_bag = buyer.find_item(item.slug)
        if in_bag:
            in_bag.quantity += quantity
        else:
            new_item = Item()
            new_item.load(item.slug)
            new_item.quantity = quantity
            buyer.add_item(new_item)

        price = self.economy.lookup_item_price(item.slug)
        total_cost = quantity * price
        self.buyer_manager.remove_money(total_cost)

    def sell_item(self, seller: NPC, item: Item, quantity: int) -> None:
        """Process selling of items."""
        remaining_quantity = item.quantity - quantity
        if remaining_quantity <= 0:
            seller.remove_item(item)
        else:
            item.quantity = remaining_quantity

        cost = self.economy.lookup_item(item.slug, "cost")
        if cost is None:
            cost = round(item.cost * self.economy.model.resale_multiplier)

        total_amount = quantity * cost
        self.seller_manager.add_money(total_amount)


def filter_inventory(
    buyer: NPC, seller: NPC, economy: Economy, is_player_buyer: bool
) -> list[Item]:
    inventory = (
        seller.items
        if is_player_buyer
        else [item for item in seller.items if item.behaviors.resellable]
    )

    if is_player_buyer:
        inventory = [
            item
            for item in inventory
            if buyer.game_variables.get(f"{economy.model.slug}:{item.slug}", 0)
            > 0
            or item.quantity == INFINITE_ITEMS
        ]

    return sorted(inventory, key=lambda x: x.name)


def generate_item_label(
    item: Item,
    economy: Economy,
    qty: Optional[int] = None,
    price: Optional[int] = None,
    seller_mode: bool = False,
) -> str:
    if seller_mode:
        cost = economy.lookup_item(item.slug, "cost") or round(
            item.cost * economy.model.resale_multiplier
        )
        return (
            f"${cost:3} {item.name} x {item.quantity}"
            if item.quantity != INFINITE_ITEMS
            else f"${cost:3} {item.name}"
        )
    else:
        qty = qty or 0
        price = price or 0
        if item.quantity != INFINITE_ITEMS:
            return (
                f"${price:4} {item.name} x {qty}"
                if qty > 0
                else f"${price:4} {T.translate('shop_buy_soldout')}"
            )
        else:
            return f"${price:4} {item.name}"
