# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from tuxemon.money.bill import BillEntry
from tuxemon.money.manager import MoneyManager

if TYPE_CHECKING:
    from tuxemon.npc import NPC, NPCState

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
        self.money_manager = decode_money(save_data["money"])

    def transfer_money_to(self, amount: int, recipient: NPC) -> None:
        self.money_manager.remove_money(amount)
        recipient.money_controller.money_manager.add_money(amount)

    def transfer_bank_to(self, amount: int, recipient: NPC) -> None:
        self.money_manager.withdraw_from_bank(amount)
        recipient.money_controller.money_manager.deposit_to_bank(amount)


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
