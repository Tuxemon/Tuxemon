# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from typing import TYPE_CHECKING

from tuxemon.item.item import Item
from tuxemon.monster.monster import Monster

if TYPE_CHECKING:
    from tuxemon.economy.shop_manager import ShopManager
    from tuxemon.entity.npc import NPC
    from tuxemon.money.manager import MoneyManager


class TransactionManager:
    """Handles all transaction operations for the shop."""

    def __init__(
        self,
        buyer_manager: MoneyManager,
        seller_manager: MoneyManager,
        shop_manager: ShopManager,
    ) -> None:
        self.buyer_manager = buyer_manager
        self.seller_manager = seller_manager
        self.shop_manager = shop_manager

    def _process_payment(self, amount: int, is_buying: bool) -> None:
        if is_buying:
            # Buyer pays, seller receives
            self.buyer_manager.remove_money(amount)
            self.seller_manager.add_money(amount)
        else:
            # Seller receives, buyer pays
            self.seller_manager.add_money(amount)
            self.buyer_manager.remove_money(amount)

    def _adjust_inventory(self, npc: NPC, item: Item, quantity: int) -> None:
        """Adds items to NPC's bag using BagHandler rules."""
        if quantity <= 0:
            return  # ignore invalid or zero quantities

        new_item = Item.create(item.slug)
        success = npc.bag.add_item(new_item, quantity)

        if not success:
            raise RuntimeError(
                f"Failed to add item '{item.slug}' x{quantity} to NPC '{npc.slug}'."
            )

    def buy_item(
        self,
        buyer: NPC,
        item: Item,
        quantity: int,
        label: str,
        cost: int,
    ) -> None:
        """Buyer purchases items from shop."""
        if not self.shop_manager.decrease_stock(label, quantity):
            raise RuntimeError(f"Insufficient stock for {label}")
        self._adjust_inventory(buyer, item, quantity)
        self._process_payment(cost, is_buying=True)

    def buy_monster(
        self,
        buyer: NPC,
        monster: Monster,
        quantity: int,
        label: str,
        cost: int,
    ) -> None:
        """Buyer purchases monsters from shop (usually restricted to 1)."""
        if quantity != 1:
            raise ValueError("Monster purchases must be quantity=1")
        if not self.shop_manager.decrease_stock(label, quantity):
            raise RuntimeError(f"Insufficient stock for {label}")
        buyer.party.add_monster(monster)
        self._process_payment(cost, is_buying=True)

    def sell_item(
        self, seller: NPC, item: Item, quantity: int, amount: int, label: str
    ) -> None:
        """Seller sells items to shop."""
        success = seller.bag.remove_item(item, quantity)
        if not success:
            raise RuntimeError(
                f"Seller '{seller.slug}' does not have enough of '{item.slug}' "
                f"to sell {quantity} units."
            )

        self.shop_manager.increase_stock(label, quantity)
        self._process_payment(amount, is_buying=False)

    def sell_monster(
        self, seller: NPC, monster: Monster, amount: int, label: str
    ) -> None:
        """Seller sells monster to shop (always quantity=1)."""
        seller.party.remove_monster(monster)
        self.shop_manager.increase_stock(label, 1)
        self._process_payment(amount, is_buying=False)
