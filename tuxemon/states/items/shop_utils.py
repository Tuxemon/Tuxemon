# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Union

from pygame.rect import Rect

from tuxemon.item.item import INFINITE_ITEMS, Item
from tuxemon.locale import T
from tuxemon.menu.formatter import CurrencyFormatter
from tuxemon.monster import Monster

if TYPE_CHECKING:
    from tuxemon.economy.economy import Economy
    from tuxemon.money import MoneyManager
    from tuxemon.npc import NPC


class TransactionManager:
    """Handles all transaction operations for the shop."""

    def __init__(
        self,
        buyer_manager: MoneyManager,
        seller_manager: MoneyManager,
    ) -> None:
        self.buyer_manager = buyer_manager
        self.seller_manager = seller_manager

    def _process_payment(self, amount: int, is_buying: bool) -> None:
        if is_buying:
            self.buyer_manager.remove_money(amount)
        else:
            self.seller_manager.add_money(amount)

    def _adjust_inventory(self, npc: NPC, item: Item, quantity: int) -> None:
        in_bag = npc.items.find_item(item.slug)
        if in_bag:
            in_bag.increase_quantity(quantity)
        else:
            new_item = Item.create(item.slug)
            npc.items.add_item(new_item, quantity)

    def _adjust_monster_party(self, npc: NPC, monster: Monster) -> None:
        npc.party.add_monster(monster)

    def buy_item(
        self, buyer: NPC, item: Item, quantity: int, label: str, cost: int
    ) -> None:
        if item.quantity != INFINITE_ITEMS:
            item.decrease_quantity(quantity)
            buyer.game_variables[label] -= quantity

        self._adjust_inventory(buyer, item, quantity)
        self._process_payment(cost * quantity, is_buying=True)

    def sell_item(
        self, seller: NPC, item: Item, quantity: int, amount: int
    ) -> None:
        seller.items.remove_item(item, quantity)
        self._process_payment(amount * quantity, is_buying=False)

    def buy_monster(
        self,
        buyer: NPC,
        monster: Monster,
        quantity: int,
        label: str,
        cost: int,
    ) -> None:
        buyer.game_variables[label] -= quantity
        self._adjust_monster_party(buyer, monster)
        self._process_payment(cost * quantity, is_buying=True)

    def sell_monster(self, seller: NPC, monster: Monster, amount: int) -> None:
        seller.party.remove_monster(monster)
        self._process_payment(amount, is_buying=False)


def calc_internal_rect(base_rect: Rect) -> Rect:
    rect = base_rect.copy()
    rect.width = int(rect.width * 0.58)
    rect.left = int(base_rect.width * 0.365)
    rect.top = int(rect.height * 0.05)
    rect.height = int(base_rect.height * 0.60)
    return rect


def filter_inventory(buyer: NPC, seller: NPC, economy: Economy) -> list[Item]:

    # Player is buying — pull from the seller's shop inventory
    if buyer.is_player:
        raw_inventory = (
            seller.shop_inventory.items if seller.shop_inventory else []
        )
        inventory = [
            item
            for item in raw_inventory
            if buyer.game_variables.get(f"{economy.model.slug}:{item.slug}", 0)
            > 0
            or item.quantity == INFINITE_ITEMS
        ]
    # Player is selling — only show resellable items in player's bag
    else:
        inventory = [
            item
            for item in seller.items.get_items()
            if item.behaviors.resellable
        ]

    return sorted(inventory, key=lambda x: x.name)


def filter_party(buyer: NPC, seller: NPC, economy: Economy) -> list[Monster]:

    # Player is buying — pull from the seller's shop inventory
    if buyer.is_player:
        raw_inventory = (
            seller.shop_inventory.monsters if seller.shop_inventory else []
        )
        inventory = [
            monster
            for monster in raw_inventory
            if buyer.game_variables.get(
                f"{economy.model.slug}:{monster.slug}", 0
            )
            > 0
        ]
    # Player is selling — only show resellable items in player's bag
    else:
        inventory = [monster for monster in seller.party.monsters]

    return sorted(inventory, key=lambda x: x.name)


def get_item_label(
    item: Item, price_tag: str, qty: int, seller_mode: bool
) -> str:
    is_infinite = item.quantity == INFINITE_ITEMS

    if seller_mode:
        return (
            f"{price_tag} {item.name}"
            if is_infinite
            else f"{price_tag} {item.name} x {item.quantity}"
        )

    if is_infinite:
        return f"{price_tag} {item.name}"
    elif qty > 0:
        return f"{price_tag} {item.name} x {qty}"
    else:
        return f"{price_tag} {T.translate('shop_buy_soldout')}"


def get_monster_label(monster: Monster, price_tag: str) -> str:
    return f"{price_tag} lv.{monster.level} {monster.name}"


def generate_label(
    entity: Union[Item, Monster],
    economy: Economy,
    qty: Optional[int] = None,
    seller_mode: bool = False,
) -> tuple[str, str, int]:
    formatter = CurrencyFormatter()
    qty = qty or 1
    safe_qty = qty if qty > 0 else 1

    total_price, discount_percent = get_final_price(
        entity, economy, qty, seller_mode
    )
    unit_price = (
        round(total_price / safe_qty) if qty != -1 else round(total_price)
    )
    price_tag = formatter.format(unit_price)
    discount_label = (
        f" ({discount_percent}% off)" if discount_percent > 0 else ""
    )

    if isinstance(entity, Item):
        label = get_item_label(entity, price_tag, qty, seller_mode)
    elif isinstance(entity, Monster):
        label = get_monster_label(entity, price_tag)

    return label, discount_label, unit_price


def get_final_price(
    entity: Union[Item, Monster],
    economy: Economy,
    quantity: int,
    seller_mode: bool = False,
) -> tuple[int, int]:
    if seller_mode:
        base_cost: float

        if isinstance(entity, Item):
            lookup_cost = economy.lookup_item_field(entity.slug, "cost")
            if lookup_cost is not None:
                base_cost = float(lookup_cost)
            else:
                base_cost = entity.cost * economy.model.resale_multiplier
        else:  # Monster
            lookup_cost = economy.get_monster_field(entity.slug, "cost")
            if lookup_cost is not None:
                base_cost = float(lookup_cost)
            else:
                base_cost = entity.hp * economy.model.resale_multiplier

        return economy.policy.apply_resell_modifiers(
            round(base_cost), quantity, entity.slug
        )

    else:
        if isinstance(entity, Item):
            lookup_price = economy.lookup_item_field(entity.slug, "price")
            if lookup_price is not None:
                base_price = lookup_price
            else:
                base_price = round(
                    entity.cost * economy.model.resale_multiplier
                )
        else:
            price = economy.get_monster_field(entity.slug, "price")
            if price is None:
                raise ValueError(f"Missing price for monster: {entity.slug}")
            base_price = price

        return economy.policy.apply_modifiers(
            base_price, quantity, entity.slug
        )
