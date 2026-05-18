# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations


class CurrencyFormatter:
    """Formats a monetary value with a currency symbol."""

    def __init__(
        self, symbol: str = "$", position: str = "before", width: int = 4
    ) -> None:
        self.symbol = symbol
        self.position = position
        self.width = width

    def format(self, amount: int) -> str:
        amount_str = f"{amount:>{self.width}}"
        if self.position == "before":
            return f"{self.symbol}{amount_str}"
        else:
            return f"{amount_str}{self.symbol}"


class QuantityFormatter:
    """Formats a quantity value with a quantity symbol."""

    def __init__(self, symbol: str = "x") -> None:
        self.symbol = symbol

    def format(self, quantity: int) -> str:
        return f"{self.symbol} {quantity}"
