# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

INFINITE_ITEMS: int = -1


class Stock:
    """Handles item quantity and consumption logic."""

    def __init__(self, quantity: int = 1):
        self.quantity = quantity

    @property
    def is_infinite(self) -> bool:
        return self.quantity == INFINITE_ITEMS

    @property
    def has_any(self) -> bool:
        return self.is_infinite or self.quantity > 0

    def set(self, amount: int) -> None:
        if amount == INFINITE_ITEMS:
            self.quantity = INFINITE_ITEMS
            return

        if amount < 0:
            amount = 0

        self.quantity = amount

    def add(self, amount: int) -> None:
        if not self.is_infinite:
            self.quantity += max(0, amount)

    def try_add(self, amount: int) -> bool:
        if amount < 0:
            return False
        if self.is_infinite:
            return True
        self.quantity += amount
        return True

    def remove(self, amount: int = 1) -> bool:
        if amount < 0:
            return False

        if self.is_infinite:
            return True

        if self.quantity >= amount:
            self.quantity -= amount
            return True

        return False

    def try_remove(self, amount: int = 1) -> bool:
        if amount < 0:
            return False
        if self.is_infinite:
            return True
        if self.quantity < amount:
            return False
        self.quantity -= amount
        return True

    def consume_one(self) -> bool:
        return self.try_remove(1)
