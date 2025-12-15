# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from functools import partial
from typing import Any, ClassVar, Optional

from pygame.surface import Surface

from tuxemon.item.item import Item
from tuxemon.item.shop_utils import (
    generate_label,
)
from tuxemon.menu.interface import MenuItem
from tuxemon.menu.quantity import QuantityAndCostMenu, QuantityAndPriceMenu
from tuxemon.states.shop_base import ShopMenuState


class ShopItemMenuState(ShopMenuState[Item]):
    """State for buying and selling items, implementing the abstract methods of the generic ShopMenuState."""

    name: ClassVar[str] = "ShopItemMenuState"

    def _get_asset_image(self, asset: MenuItem[Item]) -> Optional[Surface]:
        image = asset.game_object.surface
        return image if image else None

    def _display_asset_description(self, asset: MenuItem[Item]) -> None:
        if asset.description:
            self.dialog.alert(
                asset.description, self.text_area, dialog_speed="max"
            )

    def _filter_inventory(self) -> list[Item]:
        return self.applier.filter_items(
            self.buyer,
            self.seller,
            self.economy,
            self.client.shop_manager,
        )

    def _populate_menu(self, inventory: list[Item]) -> None:
        for item in inventory:
            if self.buyer.is_player:
                key = self.client.shop_manager.get_full_label(
                    self.economy.model.slug, item.slug
                )
                qty = self.client.shop_manager.get_quantity(key)
                label, _, price = generate_label(item, self.economy, qty)
                unavailable = price > self.buyer_manager.get_money()
                self._add_menu_item(item, label, {"price": price}, unavailable)
            elif self.seller.is_player:
                label, _, cost = generate_label(
                    item, self.economy, qty=None, seller_mode=True
                )
                self._add_menu_item(item, label, {"cost": cost})

    def _get_selection_menu_params(
        self, menu_item: MenuItem[Item]
    ) -> dict[str, Any]:
        item = menu_item.game_object
        if self.buyer.is_player:
            price: int = menu_item.metadata.get("price", 1)
            label = self.client.shop_manager.get_full_label(
                self.economy.model.slug, item.slug
            )

            def buy_item(quantity: int) -> None:
                total_price, _ = self.economy.calculate_price(item, quantity)
                self.transaction_manager.buy_item(
                    self.buyer, item, quantity, label, total_price
                )
                self.reload_shop()

            max_quantity = (
                self.client.shop_manager.get_max_affordable_quantity(
                    label, price, self.buyer_manager.get_money()
                )
            )
            return {
                "callback": partial(buy_item),
                "max_quantity": max_quantity,
                "cost": price,
            }
        elif self.seller.is_player:
            metadata_cost = menu_item.metadata.get("cost")
            item_model = self.economy.get_item(item.slug)
            basic_cost = item_model.cost if item_model else None
            if metadata_cost is not None:
                cost = metadata_cost
            elif basic_cost:
                cost = basic_cost
            else:
                cost = round(item.cost * self.economy.model.resale_multiplier)

            def sell_item(quantity: int) -> None:
                label = self.client.shop_manager.get_full_label(
                    self.economy.model.slug, item.slug
                )
                total_price, _ = self.economy.calculate_price(
                    item, quantity, seller_mode=True
                )
                self.transaction_manager.sell_item(
                    self.seller, item, quantity, total_price, label
                )
                self.reload_shop()

            return {
                "callback": partial(sell_item),
                "max_quantity": item.quantity,
                "cost": cost,
            }
        return {}


class ShopItemBuyMenuState(ShopItemMenuState):
    """State for buying items."""

    name: ClassVar[str] = "ShopItemBuyMenuState"

    def on_menu_selection(self, menu_item: MenuItem[Item]) -> None:
        item = menu_item.game_object
        price: int = menu_item.metadata.get("price", 1)
        label = self.client.shop_manager.get_full_label(
            self.economy.model.slug, item.slug
        )

        def buy_item(quantity: int) -> None:
            total_price, _ = self.economy.calculate_price(item, quantity)
            self.transaction_manager.buy_item(
                self.buyer, item, quantity, label, total_price
            )
            self.reload_items()
            if (
                self.seller.shop_inventory
                and not self.seller.shop_inventory.has_item(item.slug)
            ):
                self.on_menu_selection_change()

        max_quantity = self.client.shop_manager.get_max_affordable_quantity(
            label, price, self.buyer_manager.get_money()
        )

        self.client.state_manager.push_state(
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

    name: ClassVar[str] = "ShopItemSellMenuState"

    def on_menu_selection(self, menu_item: MenuItem[Item]) -> None:
        item = menu_item.game_object
        metadata_cost = menu_item.metadata.get("cost")
        item_model = self.economy.get_item(item.slug)
        basic_cost = item_model.cost if item_model else None

        if metadata_cost is not None:
            cost = metadata_cost
        elif basic_cost:
            cost = basic_cost
        else:
            cost = round(item.cost * self.economy.model.resale_multiplier)

        def sell_item(quantity: int) -> None:
            label = self.client.shop_manager.get_full_label(
                self.economy.model.slug, item.slug
            )
            total_price, _ = self.economy.calculate_price(
                item, quantity, seller_mode=True
            )
            self.transaction_manager.sell_item(
                self.seller, item, quantity, total_price, label
            )
            self.reload_items()
            if not self.seller.bag.has_item(item.slug):
                self.on_menu_selection_change()

        self.client.state_manager.push_state(
            QuantityAndCostMenu(
                callback=partial(sell_item),
                max_quantity=item.quantity,
                quantity=1,
                shrink_to_items=True,
                cost=cost,
            )
        )
