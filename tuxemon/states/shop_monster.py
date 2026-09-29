# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, Any, ClassVar

from pygame.surface import Surface

from tuxemon.item.shop_utils import (
    generate_label,
)
from tuxemon.menu.interface import MenuItem
from tuxemon.monster.monster import Monster
from tuxemon.monster.renderer import MonsterRenderer
from tuxemon.states.shop_base import ShopMenuState

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient
    from tuxemon.economy.economy import Economy
    from tuxemon.entity.npc import NPC


class ShopMonsterMenuState(ShopMenuState[Monster]):
    """State for buying and selling monsters, implementing the abstract methods of the generic ShopMenuState."""

    name: ClassVar[str] = "ShopMonsterMenuState"

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

    def _get_asset_image(self, asset: MenuItem[Monster]) -> Surface | None:
        renderer = MonsterRenderer(asset.game_object, scale=self.factor)
        image = renderer.get_sprite("front")
        return image.image if image else None

    def _display_asset_description(self, asset: MenuItem[Monster]) -> None:
        if asset.description:
            self.dialog.alert(
                asset.description, self.text_area, dialog_speed="max"
            )

    def _filter_inventory(self) -> list[Monster]:
        return self.applier.filter_monsters(
            self.buyer,
            self.seller,
            self.economy,
            self.client.shop_manager,
        )

    def _populate_menu(self, inventory: list[Monster]) -> None:
        for monster in inventory:
            if self.buyer.is_player:
                key = self.client.shop_manager.get_full_label(
                    self.economy.model.slug, monster.slug
                )
                qty = self.client.shop_manager.get_quantity(key)
                label, _, price = generate_label(monster, self.economy, qty)
                self._add_menu_item(monster, label, {"price": price})
            elif self.seller.is_player:
                label, _, cost = generate_label(
                    monster, self.economy, qty=None, seller_mode=True
                )
                self._add_menu_item(monster, label, {"cost": cost})

    def _get_selection_menu_params(
        self, menu_item: MenuItem[Monster]
    ) -> dict[str, Any]:
        monster = menu_item.game_object
        if self.buyer.is_player:
            price: int = menu_item.metadata.get("price", 1)
            label = self.client.shop_manager.get_full_label(
                self.economy.model.slug, monster.slug
            )

            def buy_monster(quantity: int) -> None:
                price = self.economy.calculate_price(monster, quantity)
                self.transaction_manager.buy_monster(
                    self.buyer, monster, quantity, label, price.final_price
                )
                self.reload_shop()

            max_quantity = (
                self.client.shop_manager.get_max_affordable_quantity(
                    label, price, self.buyer_manager.get_money()
                )
            )
            return {
                "callback": partial(buy_monster),
                "max_quantity": max_quantity,
                "cost": price,
            }
        elif self.seller.is_player:
            metadata_cost = menu_item.metadata.get("cost")
            monster_model = self.economy.get_monster(monster.slug)
            basic_cost = monster_model.cost if monster_model else None
            if metadata_cost is not None:
                cost = metadata_cost
            elif basic_cost:
                cost = basic_cost
            else:
                cost = round(monster.hp * self.economy.model.resale_multiplier)

            def sell_monster(quantity: int) -> None:
                label = self.client.shop_manager.get_full_label(
                    self.economy.model.slug, monster.slug
                )
                price = self.economy.calculate_price(
                    monster, quantity, seller_mode=True
                )
                self.transaction_manager.sell_monster(
                    self.seller, monster, price.final_price, label
                )
                self.reload_shop()

            return {
                "callback": partial(sell_monster),
                "max_quantity": 1,
                "cost": cost,
            }
        return {}


class ShopMonsterBuyMenuState(ShopMonsterMenuState):
    """State for buying monsters."""

    name: ClassVar[str] = "ShopMonsterBuyMenuState"

    def __init__(self, client: BaseClient, *args: Any, **kwargs: Any):
        super().__init__(client, *args, **kwargs)

    def on_menu_selection(self, menu_monster: MenuItem[Monster]) -> None:
        monster = menu_monster.game_object
        price: int = menu_monster.metadata.get("price", 1)
        label = self.client.shop_manager.get_full_label(
            self.economy.model.slug, monster.slug
        )

        def buy_monster(quantity: int) -> None:
            price = self.economy.calculate_price(monster, quantity)
            if price.final_price > self.buyer_manager.get_money():
                return

            self.transaction_manager.buy_monster(
                self.buyer, monster, quantity, label, price.final_price
            )
            self.reload_items()
            if (
                self.seller.shop_inventory
                and not self.seller.shop_inventory.has_monster(monster.slug)
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
            callback=partial(buy_monster),
            price=price,
            wallet_money=self.buyer_manager.get_money(),
        )


class ShopMonsterSellMenuState(ShopMonsterMenuState):
    """State for selling monsters."""

    name: ClassVar[str] = "ShopMonsterSellMenuState"

    def __init__(self, client: BaseClient, *args: Any, **kwargs: Any):
        super().__init__(client, *args, **kwargs)

    def on_menu_selection(self, menu_monster: MenuItem[Monster]) -> None:
        monster = menu_monster.game_object
        metadata_cost = menu_monster.metadata.get("cost")
        monster_model = self.economy.get_monster(monster.slug)
        basic_cost = monster_model.cost if monster_model else None

        if metadata_cost is not None:
            cost = metadata_cost
        elif basic_cost:
            cost = basic_cost
        else:
            cost = round(monster.hp * self.economy.model.resale_multiplier)

        def sell_monster(quantity: int) -> None:
            label = self.client.shop_manager.get_full_label(
                self.economy.model.slug, monster.slug
            )
            price = self.economy.calculate_price(
                monster, quantity, seller_mode=True
            )
            self.transaction_manager.sell_monster(
                self.seller, monster, price.final_price, label
            )
            self.reload_items()
            if not self.seller.party.has_monster(monster):
                self.on_menu_selection_change()

        self.client.state_manager.push_state(
            "QuantityPickerState",
            client=self.client,
            min_value=1,
            max_value=1,
            start_value=1,
            step=1,
            callback=partial(sell_monster),
            cost=cost,
            wallet_money=self.seller_manager.get_money(),
        )
