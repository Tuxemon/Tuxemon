# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Mapping

from tuxemon.money.bill import BillEntry
from tuxemon.money.portfolio import PortfolioManager

logger = logging.getLogger(__name__)


class MoneyManager:
    def __init__(self) -> None:
        self.money: int = 0
        self.bank_account: int = 0
        self.bills: dict[str, BillEntry] = {}
        self.portfolio_manager: PortfolioManager = PortfolioManager()

    def set_money(self, amount: int) -> None:
        if amount < 0:
            raise AttributeError(f"{amount} must be >= 0")
        self.money = amount

    def add_money(self, amount: int) -> None:
        self.money += amount
        if self.money < 0:
            logger.warning(
                f"Money underflow: clamped to 0 after subtracting {amount}"
            )
            self.money = 0

    def remove_money(self, amount: int) -> None:
        self.money -= amount
        if self.money < 0:
            logger.warning(
                f"Money underflow: clamped to 0 after subtracting {amount}"
            )
            self.money = 0

    def get_money(self) -> int:
        return self.money

    def deposit_to_bank(self, amount: int) -> None:
        self.bank_account += amount

    def withdraw_from_bank(self, amount: int) -> None:
        if self.bank_account >= amount:
            self.bank_account -= amount
        else:
            raise ValueError("Insufficient funds in bank account")

    def get_bank_balance(self) -> int:
        return self.bank_account

    def set_bill(
        self,
        bill_name: str,
        amount: int,
        interest_rate: float | None = None,
        late_fee: int | None = None,
        share_rate: float | None = None,
    ) -> None:
        self.bills[bill_name] = BillEntry(
            amount=amount,
            interest_rate=interest_rate,
            late_fee=late_fee,
            share_rate=share_rate,
        )

    def add_bill(self, bill_name: str, amount: int) -> None:
        if bill_name not in self.bills:
            raise KeyError(
                f"Method 'add_bill' failed. No such bill: {bill_name}"
            )

        self.bills[bill_name].amount += amount

    def remove_bill(self, bill_name: str, amount: int) -> None:
        if bill_name not in self.bills:
            raise KeyError(
                f"Method 'remove_bill' failed. No such bill: {bill_name}"
            )

        self.bills[bill_name].amount -= amount
        if self.bills[bill_name].amount <= 0:
            del self.bills[bill_name]

    def pay_bill_with_money(self, bill_name: str, amount: int) -> None:
        if bill_name not in self.bills:
            raise KeyError(
                f"Method 'pay_bill_with_money' failed. No such bill: {bill_name}"
            )

        bill = self.bills[bill_name]
        payment = min(amount, bill.amount)

        self.remove_money(payment)
        self.remove_bill(bill_name, payment)

    def pay_bill_with_deposit(self, bill_name: str, amount: int) -> None:
        if bill_name not in self.bills:
            raise KeyError(
                f"Method 'pay_bill_with_deposit' failed. No such bill: {bill_name}"
            )

        bill = self.bills[bill_name]
        payment = min(amount, bill.amount)

        self.withdraw_from_bank(payment)
        self.remove_bill(bill_name, payment)

    def get_bills(self) -> dict[str, BillEntry]:
        return self.bills

    def get_bill(self, bill_name: str) -> BillEntry | None:
        return self.bills.get(bill_name)

    def get_total_bills(self) -> int:
        return sum(bill.amount for bill in self.bills.values())

    def get_total_wealth(self, market_prices: Mapping[str, float]) -> int:
        portfolio_value = self.portfolio_manager.get_portfolio_value(
            market_prices
        )
        return int(self.money + self.bank_account + portfolio_value)

    def transfer_all_money_to_bank(self) -> None:
        self.deposit_to_bank(self.money)
        self.money = 0

    def withdraw_all_money_from_bank(self) -> None:
        self.money += self.bank_account
        self.bank_account = 0

    def apply_bank_interest(self, interest_rate: float) -> None:
        if interest_rate < 0:
            raise ValueError("Interest rate must be non-negative")
        interest = int(self.bank_account * interest_rate)
        self.bank_account += interest

    def apply_interest_to_bill(self, bill_name: str) -> None:
        if bill_name not in self.bills:
            raise KeyError(
                f"Method 'apply_interest_to_bill' failed. No such bill: {bill_name}"
            )

        self.bills[bill_name].apply_interest()

    def apply_late_fee_to_bill(self, bill_name: str) -> None:
        if bill_name not in self.bills:
            raise KeyError(
                f"Method 'apply_late_fee_to_bill' failed. No such bill: {bill_name}"
            )

        self.bills[bill_name].apply_late_fee()

    def apply_share_to_bill(self, bill_name: str, earnings: int) -> int:
        if bill_name not in self.bills:
            raise KeyError(
                f"Method 'apply_share_to_bill' failed. No such bill: {bill_name}"
            )

        bill = self.bills[bill_name]
        remaining_earnings = bill.apply_share(earnings)

        if bill.amount <= 0:
            del self.bills[bill_name]

        return remaining_earnings

    def apply_all_battle_shares(self, earnings: int) -> int:
        """
        Applies share deductions from battle earnings to all active bills.
        Bills with zero or negative amount are removed.
        Returns the remaining earnings after all deductions.
        """
        for bill_name in list(self.bills.keys()):
            bill = self.bills[bill_name]
            earnings = bill.apply_share(earnings)
            if bill.amount <= 0:
                del self.bills[bill_name]
        return earnings

    def buy_investment(self, symbol: str, shares: int, price: float) -> None:
        """Buys investment shares using money from the bank account."""
        total_cost = self.portfolio_manager.buy_shares(symbol, shares, price)
        self.withdraw_from_bank(int(total_cost))

    def sell_investment(self, symbol: str, shares: int, price: float) -> None:
        """Sells investment shares and deposits the revenue into the bank account."""
        total_revenue = self.portfolio_manager.sell_shares(
            symbol, shares, price
        )
        self.deposit_to_bank(int(total_revenue))
