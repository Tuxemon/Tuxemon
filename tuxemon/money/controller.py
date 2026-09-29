# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from tuxemon.money.bill import BillEntry
from tuxemon.money.manager import MoneyManager
from tuxemon.money.portfolio import PortfolioManager

if TYPE_CHECKING:
    from tuxemon.entity.npc import NPC
    from tuxemon.save_system.save_state import NPCState

logger = logging.getLogger(__name__)


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
        self.money_manager = decode_money(save_data.money or {})

    def transfer_money_to(self, amount: int, recipient: NPC) -> None:
        if amount <= 0:
            raise ValueError("Transfer amount must be positive")

        if self.money_manager.get_money() < amount:
            raise ValueError(
                f"Insufficient funds: tried to transfer {amount}, "
                f"but only {self.money_manager.get_money()} available"
            )

        self.money_manager.remove_money(amount)
        recipient.money_controller.money_manager.add_money(amount)

    def transfer_bank_to(self, amount: int, recipient: NPC) -> None:
        if amount <= 0:
            raise ValueError("Transfer amount must be positive")

        if self.money_manager.get_bank_balance() < amount:
            raise ValueError(
                f"Insufficient bank funds: tried to transfer {amount}, "
                f"but only {self.money_manager.get_bank_balance()} available"
            )

        self.money_manager.withdraw_from_bank(amount)
        recipient.money_controller.money_manager.deposit_to_bank(amount)


def decode_money(json_data: Mapping[str, Any]) -> MoneyManager:
    money_manager = MoneyManager()
    if not json_data:
        return money_manager

    money_manager.money = json_data.get("money", 0)
    money_manager.bank_account = json_data.get("bank_account", 0)

    bills = json_data.get("bills", {})
    for bill_name, bill_data in bills.items():
        entry = BillEntry(**bill_data)
        money_manager.bills[bill_name] = entry

    portfolio_data = json_data.get("portfolio", {})
    money_manager.portfolio_manager = PortfolioManager.from_state(
        portfolio_data
    )

    return money_manager


def encode_money(money_manager: MoneyManager) -> Mapping[str, Any]:
    return {
        "money": money_manager.money,
        "bank_account": money_manager.bank_account,
        "bills": {
            bill_name: bill_entry.get_state()
            for bill_name, bill_entry in money_manager.bills.items()
        },
        "portfolio": money_manager.portfolio_manager.get_state(),
    }
