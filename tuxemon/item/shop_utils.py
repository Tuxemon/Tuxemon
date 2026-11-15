# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from typing import TYPE_CHECKING

from pygame.rect import Rect

from tuxemon.item.item import Item
from tuxemon.item.stock import INFINITE_ITEMS
from tuxemon.locale.locale import T
from tuxemon.menu.formatter import CurrencyFormatter
from tuxemon.monster.monster import Monster

if TYPE_CHECKING:
    from tuxemon.economy.economy import Economy


def calc_internal_rect(base_rect: Rect) -> Rect:
    rect = base_rect.copy()
    rect.width = int(rect.width * 0.58)
    rect.left = int(base_rect.width * 0.365)
    rect.top = int(rect.height * 0.05)
    rect.height = int(base_rect.height * 0.60)
    return rect


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
    entity: Item | Monster,
    economy: Economy,
    qty: int | None = None,
    seller_mode: bool = False,
) -> tuple[str, str, int]:
    """
    Build a display label for an Item or Monster.

    Returns:
        (label, discount_label, unit_price)
    """
    formatter = CurrencyFormatter()
    qty = qty or 1
    safe_qty = qty if qty > 0 else 1

    price = economy.calculate_price(entity, qty, seller_mode)
    unit_price = (
        round(price.final_price / safe_qty)
        if qty != -1
        else round(price.final_price)
    )
    price_tag = formatter.format(unit_price)
    discount_label = (
        f" ({price.modifier_percent}% off)"
        if price.modifier_percent > 0
        else ""
    )

    if isinstance(entity, Item):
        label = get_item_label(entity, price_tag, qty, seller_mode)
    elif isinstance(entity, Monster):
        label = get_monster_label(entity, price_tag)

    return label, discount_label, unit_price
