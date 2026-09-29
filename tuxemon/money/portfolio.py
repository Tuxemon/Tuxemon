# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


@dataclass
class Investment:
    symbol: str
    shares: int
    purchase_price: float

    @property
    def total_cost_basis(self) -> float:
        """Calculates the total money spent to acquire these shares."""
        return round(self.shares * self.purchase_price, 4)


class PortfolioManager:
    """Manages an NPC's investment portfolio."""

    def __init__(self) -> None:
        self.investments: dict[str, Investment] = {}

    def buy_shares(self, symbol: str, shares: int, price: float) -> float:
        """Buys shares of an investment and returns the total cost."""
        symbol = symbol.upper()

        if not symbol.isalnum():
            raise ValueError("Invalid symbol format.")

        if shares <= 0 or price <= 0:
            raise ValueError("Shares and price must be positive.")

        total_cost = shares * price

        if symbol in self.investments:
            current = self.investments[symbol]
            new_shares = current.shares + shares

            new_purchase_price = (
                (current.shares * current.purchase_price) + total_cost
            ) / new_shares

            current.shares = new_shares
            current.purchase_price = new_purchase_price
        else:
            self.investments[symbol] = Investment(
                symbol=symbol, shares=shares, purchase_price=price
            )

        return total_cost

    def sell_shares(self, symbol: str, shares: int, price: float) -> float:
        """Sells shares of an investment and returns the total revenue."""
        symbol = symbol.upper()

        if not symbol.isalnum():
            raise ValueError("Invalid symbol format.")

        if symbol not in self.investments:
            raise KeyError(f"No such investment: {symbol}")

        if shares <= 0:
            raise ValueError("Shares must be positive.")

        investment = self.investments[symbol]
        if shares > investment.shares:
            raise ValueError("Insufficient shares to sell.")

        total_revenue = shares * price
        investment.shares -= shares

        if investment.shares == 0:
            del self.investments[symbol]

        return total_revenue

    def get_portfolio_value(self, market_prices: Mapping[str, float]) -> float:
        """Calculates the total market value of the portfolio."""
        total_value = 0.0
        for symbol, investment in self.investments.items():
            if symbol in market_prices:
                total_value += investment.shares * market_prices[symbol]
        return total_value

    def calculate_profit_loss(
        self, market_prices: Mapping[str, float]
    ) -> float:
        """Calculates the unrealized profit or loss (P&L) of the entire portfolio."""
        total_market_value = self.get_portfolio_value(market_prices)

        total_cost_basis = sum(
            inv.total_cost_basis for inv in self.investments.values()
        )

        # P&L = Market Value - Cost Basis
        return total_market_value - total_cost_basis

    def get_state(self) -> dict[str, Any]:
        """Returns a savable state of the portfolio."""
        return {
            "investments": [
                {
                    "symbol": inv.symbol,
                    "shares": inv.shares,
                    "purchase_price": inv.purchase_price,
                }
                for inv in self.investments.values()
            ]
        }

    @classmethod
    def from_state(cls, state: dict[str, Any]) -> PortfolioManager:
        """Recreates a PortfolioManager from a saved state."""
        manager = cls()
        if "investments" in state:
            for inv_data in state["investments"]:
                symbol = inv_data["symbol"].upper()
                manager.investments[symbol] = Investment(
                    symbol=symbol,
                    shares=inv_data["shares"],
                    purchase_price=inv_data["purchase_price"],
                )
        return manager


class MarketDataManager:
    def __init__(self) -> None:
        self.prices: dict[str, float] = {}
        self.volatility: float = 0.02  # 2% standard deviation per tick

    def tick(self, dt: float) -> None:
        """Updates all prices based on elapsed time."""
        for symbol, price in list(self.prices.items()):
            change = random.gauss(0, self.volatility) * dt
            new_price = price * (1 + change)

            if new_price > 0:
                self.prices[symbol] = new_price

    def get_price(self, symbol: str) -> float:
        """Returns the current market price of the given symbol, or 0.0 if unavailable."""
        return self.prices.get(symbol, 0.0)

    def update_prices(self, price_map: dict[str, float]) -> None:
        """Updates market prices for multiple symbols using the provided price map."""
        for symbol, price in price_map.items():
            self.set_price(symbol, price)

    def set_price(self, symbol: str, price: float) -> None:
        """Sets the market price for the given symbol."""
        symbol = self._validate_and_normalize_symbol(symbol)

        if price > 0:
            self.prices[symbol] = price
        else:
            raise ValueError("Price must be positive.")

    def apply_fluctuation(self, symbol: str, percentage_change: float) -> None:
        """Changes the price of a symbol by a percentage."""
        symbol = self._validate_and_normalize_symbol(symbol)  # Use helper

        current_price = self.get_price(symbol)
        if current_price > 0:
            new_price = current_price * (1 + percentage_change)

            if new_price <= 0:
                raise ValueError(
                    "Price fluctuation would result in a non-positive price."
                )

            self.set_price(symbol, new_price)

    def _validate_and_normalize_symbol(self, symbol: str) -> str:
        """Checks symbol format and converts to uppercase."""
        symbol = symbol.upper()
        if not symbol.isalnum():
            raise ValueError(
                "Invalid symbol format. Symbols must be alphanumeric."
            )
        return symbol
