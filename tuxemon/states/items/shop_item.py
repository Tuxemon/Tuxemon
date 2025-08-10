# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Generator
from functools import partial
from typing import TYPE_CHECKING, Optional

from pygame.rect import Rect

from tuxemon import prepare, tools
from tuxemon.item.item import INFINITE_ITEMS, Item
from tuxemon.menu.interface import MenuItem
from tuxemon.menu.menu import Menu
from tuxemon.menu.quantity import QuantityAndCostMenu, QuantityAndPriceMenu
from tuxemon.platform.const import buttons
from tuxemon.platform.events import PlayerInput
from tuxemon.sprite import Sprite
from tuxemon.states.items.shop_utils import (
    TransactionManager,
    calc_internal_rect,
    filter_inventory,
    generate_label,
)
from tuxemon.ui.paginator import Paginator
from tuxemon.ui.text import TextArea

if TYPE_CHECKING:
    from tuxemon.economy.economy import Economy
    from tuxemon.npc import NPC


class ShopItemMenuState(Menu[Item]):
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
            self.buyer_manager, self.seller_manager
        )
        self.paginator = Paginator(self.inventory, prepare.MAX_MENU_ITEMS)

    def calc_internal_rect(self) -> Rect:
        return calc_internal_rect(self.rect)

    def is_valid_entry(self, item: Optional[Item]) -> bool:
        """Check if the selected item is valid for purchase or sale."""
        if not item:
            return False
        if self.buyer.isplayer:
            _, _, price = generate_label(item, self.economy, 1)
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
                self.dialog.alert(item.description, dialog_speed="max")

    def generate_label(
        self,
        item: Item,
        qty: Optional[int] = None,
        seller_mode: bool = False,
    ) -> tuple[str, str, int]:
        """Generate the label for shop items, handling both buyer and seller modes."""
        return generate_label(item, self.economy, qty, seller_mode)

    def _populate_menu_items(
        self, inventory: list[Item]
    ) -> Generator[MenuItem[Item], None, None]:
        for item in inventory:
            if self.buyer.isplayer:
                key = f"{self.economy.model.slug}:{item.slug}"
                qty = self.buyer.game_variables.get(key, 0)
                label, discount, price = self.generate_label(item, qty)
                fg = (
                    self.unavailable_color_shop
                    if price > self.buyer_manager.get_money()
                    else None
                )
                image = self.shadow_text(label, fg=fg)
                menu_item = MenuItem(image, item.name, item.description, item)
                yield menu_item
                menu_item.metadata["price"] = price
                self.add(menu_item)
            elif self.seller.isplayer:
                label, discount, cost = self.generate_label(
                    item, qty=None, seller_mode=True
                )
                image = self.shadow_text(label)
                menu_item = MenuItem(image, item.name, item.description, item)
                yield menu_item
                menu_item.metadata["cost"] = cost
                self.add(menu_item)

    def initialize_items(self) -> Generator[MenuItem[Item], None, None]:
        self.inventory = filter_inventory(
            self.buyer, self.seller, self.economy
        )
        if not self.inventory:
            return

        self.paginator.update_items(self.inventory)
        self.total_pages = self.paginator.total_pages()
        self.current_page = max(
            0, min(self.current_page, self.total_pages - 1)
        )

        paged_inventory = self.paginator.paginate(self.current_page)
        yield from self._populate_menu_items(paged_inventory)

    def reload_shop(self) -> None:
        self.clear()
        self.inventory = filter_inventory(
            self.buyer, self.seller, self.economy
        )

        paged_inventory = self.paginator.paginate(self.current_page)
        # Force generator execution
        list(self._populate_menu_items(paged_inventory))

        self.selected_index = (
            min(self.selected_index, len(self.menu_items) - 1)
            if self.menu_items
            else -1
        )
        self.on_menu_selection_change()

    def process_event(self, event: PlayerInput) -> Optional[PlayerInput]:
        total_pages = self.paginator.total_pages()

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


class ShopItemBuyMenuState(ShopItemMenuState):
    """State for buying items."""

    def on_menu_selection(self, menu_item: MenuItem[Item]) -> None:
        item = menu_item.game_object
        price: int = menu_item.metadata.get("price", 1)
        label = f"{self.economy.model.slug}:{item.slug}"

        def buy_item(quantity: int) -> None:
            self.transaction_manager.buy_item(
                self.buyer, item, quantity, label, price
            )
            self.reload_items()
            if (
                self.seller.shop_inventory
                and not self.seller.shop_inventory.has_item(item.slug)
            ):
                self.on_menu_selection_change()

        money = self.buyer_manager.get_money()
        qty_can_afford = int(money / price)
        inventory = self.buyer.game_variables.get(label, INFINITE_ITEMS)
        max_quantity = (
            qty_can_afford
            if inventory == INFINITE_ITEMS
            else min(qty_can_afford, inventory)
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


class ShopItemSellMenuState(ShopItemMenuState):
    """State for selling items."""

    def on_menu_selection(self, menu_item: MenuItem[Item]) -> None:
        item = menu_item.game_object
        metadata_cost = menu_item.metadata.get("cost")
        basic_cost = self.economy.lookup_item_field(item.slug, "cost")

        if metadata_cost is not None:
            cost = metadata_cost
        elif basic_cost:
            cost = basic_cost
        else:
            cost = round(item.cost * self.economy.model.resale_multiplier)

        def sell_item(quantity: int) -> None:
            self.transaction_manager.sell_item(
                self.seller, item, quantity, cost
            )
            self.reload_items()
            if not self.seller.items.has_item(item.slug):
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
