# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, Any, ClassVar

from pygame.surface import Surface

from tuxemon.item.item import Item
from tuxemon.item.shop_utils import (
    generate_label,
)
from tuxemon.menu.interface import MenuItem
from tuxemon.states.shop_base import ShopMenuState

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient
    from tuxemon.economy.economy import Economy
    from tuxemon.entity.npc import NPC


class ShopItemMenuState(ShopMenuState[Item]):
    """State for buying and selling items, implementing the abstract methods of the generic ShopMenuState."""

    name: ClassVar[str] = "ShopItemMenuState"

    def __init__(
        self,
        client: BaseClient,
        buyer: NPC,
        seller: NPC,
        economy: Economy,
        **kwargs: Any,
    ) -> None:
        super().__init__(client, buyer, seller, economy, **kwargs)
        self.update_background(self.economy.model.background)

    def _get_asset_image(self, asset: MenuItem[Item]) -> Surface | None:
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
                self._add_menu_item(item, label, {"price": price})
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
                price = self.economy.calculate_price(item, quantity)
                self.transaction_manager.buy_item(
                    self.buyer, item, quantity, label, price.final_price
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
                price = self.economy.calculate_price(
                    item, quantity, seller_mode=True
                )
                self.transaction_manager.sell_item(
                    self.seller, item, quantity, price.final_price, label
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

    def __init__(self, client: BaseClient, *args: Any, **kwargs: Any):
        super().__init__(client, *args, **kwargs)

    def on_menu_selection(self, menu_item: MenuItem[Item]) -> None:
        item = menu_item.game_object
        price: int = menu_item.metadata.get("price", 1)
        label = self.client.shop_manager.get_full_label(
            self.economy.model.slug, item.slug
        )

        def buy_item(quantity: int) -> None:
            price = self.economy.calculate_price(item, quantity)
            if price.final_price > self.buyer_manager.get_money():
                return

            self.transaction_manager.buy_item(
                self.buyer, item, quantity, label, price.final_price
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
            "QuantityPickerState",
            client=self.client,
            min_value=1,
            max_value=max_quantity,
            start_value=1,
            step=1,
            callback=partial(buy_item),
            price=price,
            wallet_money=self.buyer_manager.get_money(),
        )


class ShopItemSellMenuState(ShopItemMenuState):
    """State for selling items."""

    name: ClassVar[str] = "ShopItemSellMenuState"

    def __init__(self, client: BaseClient, *args: Any, **kwargs: Any):
        super().__init__(client, *args, **kwargs)

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
            price = self.economy.calculate_price(
                item, quantity, seller_mode=True
            )
            self.transaction_manager.sell_item(
                self.seller, item, quantity, price.final_price, label
            )
            self.reload_items()
            if not self.seller.bag.has_item(item.slug):
                self.on_menu_selection_change()

        self.client.state_manager.push_state(
            "QuantityPickerState",
            client=self.client,
            min_value=1,
            max_value=item.quantity,
            start_value=1,
            step=1,
            callback=partial(sell_item),
            cost=cost,
            wallet_money=self.seller_manager.get_money(),
        )
