# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class BillEntry:
    amount: int = 0
    interest_rate: float | None = None
    late_fee: int | None = None
    share_rate: float | None = None

    def get_state(self) -> dict[str, Any]:
        state: dict[str, Any] = {"amount": self.amount}
        if self.interest_rate is not None:
            state["interest_rate"] = self.interest_rate
        if self.late_fee is not None:
            state["late_fee"] = self.late_fee
        return state

    def apply_interest(self) -> None:
        """Apply interest based on current amount."""
        if (
            self.amount > 0
            and self.interest_rate is not None
            and self.interest_rate > 0
        ):
            interest = int(self.amount * self.interest_rate)
            self.amount += interest

    def apply_late_fee(self) -> None:
        """Apply a flat late fee."""
        if self.amount > 0 and self.late_fee is not None and self.late_fee > 0:
            self.amount += self.late_fee

    def apply_share(self, earnings: int) -> int:
        """
        Deduct a share of earnings and apply it to the bill.
        Returns the remaining earnings after deduction.
        """
        if (
            self.amount > 0
            and self.share_rate is not None
            and self.share_rate > 0
        ):
            deduction = int(earnings * self.share_rate)
            self.amount -= deduction
            if self.amount < 0:
                self.amount = 0
            return earnings - deduction
        return earnings
