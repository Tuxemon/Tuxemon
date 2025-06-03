# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from tuxemon.npc import NPC, NPCState

logger = logging.getLogger(__name__)


@dataclass
class BillEntry:
    amount: int = 0

    def get_state(self) -> dict[str, Any]:
        return {
            "amount": self.amount,
        }


class MoneyController:
    """Manages the money for an NPC."""

    def __init__(self, npc: NPC) -> None:
        self.npc = npc
        self.money_manager = MoneyManager()

    def save(self) -> Mapping[str, Any]:
        """Prepares a dictionary of the money manager to be saved to a file."""
        return encode_money(self.money_manager)

    def load(self, save_data: NPCState) -> None:
        """Recreates money manager from saved data."""
        self.money_manager = decode_money(save_data["money"])

    def transfer_money_to(self, amount: int, recipient: NPC) -> None:
        self.money_manager.remove_money(amount)
        recipient.money_controller.money_manager.add_money(amount)

    def transfer_bank_to(self, amount: int, recipient: NPC) -> None:
        self.money_manager.withdraw_from_bank(amount)
        recipient.money_controller.money_manager.deposit_to_bank(amount)


class MoneyManager:
    def __init__(self) -> None:
        self.money: int = 0
        self.bank_account: int = 0
        self.bills: dict[str, BillEntry] = {}

    def add_money(self, amount: int) -> None:
        self.money += amount
        if self.money < 0:
            self.money = 0

    def remove_money(self, amount: int) -> None:
        self.money -= amount
        if self.money < 0:
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

    def add_entry(self, bill_name: str, amount: int) -> None:
        self.bills[bill_name] = BillEntry(amount)

    def add_bill(self, bill_name: str, amount: int) -> None:
        if bill_name in self.bills:
            self.bills[bill_name].amount += amount
        else:
            self.bills[bill_name] = BillEntry(amount)

    def remove_bill(self, bill_name: str, amount: int) -> None:
        if bill_name in self.bills:
            self.bills[bill_name].amount += amount
            if self.bills[bill_name].amount < 0:
                del self.bills[bill_name]
        else:
            raise KeyError(f"No such bill: {bill_name}")

    def pay_bill_with_money(self, bill_name: str, amount: int) -> None:
        if bill_name in self.bills:
            self.remove_money(amount)
            self.remove_bill(bill_name, -abs(amount))
        else:
            raise KeyError(f"No such bill: {bill_name}")

    def pay_bill_with_deposit(self, bill_name: str, amount: int) -> None:
        if bill_name in self.bills:
            self.withdraw_from_bank(amount)
            self.remove_bill(bill_name, -abs(amount))
        else:
            raise KeyError(f"No such bill: {bill_name}")

    def get_bills(self) -> dict[str, BillEntry]:
        return self.bills

    def get_bill(self, bill_name: str) -> BillEntry:
        return self.bills.get(bill_name, BillEntry())

    def get_total_bills(self) -> int:
        return sum(bill.amount for bill in self.bills.values())

    def get_total_wealth(self) -> int:
        return self.money + self.bank_account

    def transfer_all_money_to_bank(self) -> None:
        self.deposit_to_bank(self.money)
        self.money = 0

    def withdraw_all_money_from_bank(self) -> None:
        self.money += self.bank_account
        self.bank_account = 0


def decode_money(json_data: Mapping[str, Any]) -> MoneyManager:
    money_manager = MoneyManager()
    if json_data:
        money_manager.money = json_data.get("money", 0)
        money_manager.bank_account = json_data.get("bank_account", 0)
        bills = json_data.get("bills", {})
        for bill_name, bill_data in bills.items():
            entry = BillEntry(**bill_data)
            money_manager.bills[bill_name] = entry
    return money_manager


def encode_money(money_manager: MoneyManager) -> Mapping[str, Any]:
    return {
        "money": money_manager.money,
        "bank_account": money_manager.bank_account,
        "bills": {
            bill_name: bill_entry.get_state()
            for bill_name, bill_entry in money_manager.bills.items()
        },
    }
