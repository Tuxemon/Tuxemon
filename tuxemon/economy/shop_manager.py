# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from typing import Any

from tuxemon.item.stock import INFINITE_ITEMS

logger = logging.getLogger(__name__)


@dataclass
class StockEntry:
    quantity: int = 0


class ShopManager:
    """
    Manages the persistent stock levels for all dynamic shops across the game.

    Stock is stored as a dictionary mapping a unique label (economy_slug:entity_slug)
    to StockEntry objects. This structure is serialized and saved with the game session data.
    """

    def __init__(
        self, stock_data: dict[str, StockEntry] | None = None
    ) -> None:
        self._stock: dict[str, StockEntry] = (
            stock_data if stock_data is not None else {}
        )

    def dump_to_dict(self) -> dict[str, dict[str, Any]]:
        return {k: asdict(v) for k, v in self._stock.items()}

    @staticmethod
    def load_from_dict(
        stock_data: dict[str, dict[str, Any]],
    ) -> ShopManager:
        parsed = {k: StockEntry(**v) for k, v in stock_data.items()}
        return ShopManager(stock_data=parsed)

    def is_available(self, full_label: str) -> bool:
        """
        Returns True if the given label has stock available.
        Considers both finite and infinite inventory.
        """
        qty = self.get_quantity(full_label)
        return qty == INFINITE_ITEMS or qty > 0

    def get_full_label(self, economy_slug: str, entity_slug: str) -> str:
        """Helper to generate the unique lookup key."""
        return f"{economy_slug}:{entity_slug}"

    def get_quantity(self, full_label: str) -> int:
        """Return the quantity for a given label, or 0 if not set."""
        entry = self._stock.get(full_label)
        if entry and entry.quantity == INFINITE_ITEMS:
            return INFINITE_ITEMS
        return entry.quantity if entry else 0

    def set_quantity(self, full_label: str, quantity: int) -> None:
        """Update or create a StockEntry with the given quantity."""
        if full_label in self._stock:
            self._stock[full_label].quantity = quantity
        else:
            self._stock[full_label] = StockEntry(quantity=quantity)

    def get_stock_data(self) -> dict[str, StockEntry]:
        """Return the raw StockEntry dictionary"""
        return self._stock

    def get_or_set_default(
        self, full_label: str, default_quantity: int
    ) -> int:
        """
        Retrieves the stock quantity. If it doesn't exist, sets a new StockEntry
        with the default quantity and returns it.
        """
        if full_label not in self._stock:
            self._stock[full_label] = StockEntry(quantity=default_quantity)
            return default_quantity
        return self._stock[full_label].quantity

    def get_max_affordable_quantity(
        self, label: str, unit_price: int, buyer_money: int
    ) -> int:
        """
        Returns the maximum quantity the buyer can afford for a given item label.
        Considers both buyer's money and shop inventory.
        """
        qty_can_afford = buyer_money // unit_price
        inventory = self.get_quantity(label)

        if inventory == INFINITE_ITEMS:
            return qty_can_afford
        return min(qty_can_afford, inventory)

    def decrease_stock(self, full_label: str, amount: int) -> bool:
        """Decreases stock. Returns True on success, False if stock is insufficient."""
        if amount <= 0:
            return True

        current_quantity = self.get_quantity(full_label)

        # If stock is infinite, transaction succeeds without changing the stored value
        if current_quantity == INFINITE_ITEMS:
            return True

        if current_quantity >= amount:
            new_quantity = current_quantity - amount
            self.set_quantity(full_label, new_quantity)
            logger.debug(
                f"Stock decreased for '{full_label}': {current_quantity} -> {new_quantity}"
            )
            return True

        # Insufficient stock
        logger.warning(
            f"Stock insufficient for '{full_label}'. Needed: {amount}, Available: {current_quantity}"
        )
        return False

    def increase_stock(self, full_label: str, amount: int) -> None:
        """Increases stock (used when the player sells to the shop)."""
        if amount <= 0:
            return

        current_quantity = self.get_quantity(full_label)

        # Do not increase stock if it's currently marked as infinite/unlimited
        if current_quantity == INFINITE_ITEMS:
            return

        new_quantity = current_quantity + amount
        self.set_quantity(full_label, new_quantity)
        logger.debug(
            f"Stock increased for '{full_label}': {current_quantity} -> {new_quantity}"
        )
