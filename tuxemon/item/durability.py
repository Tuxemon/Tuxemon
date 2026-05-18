# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random


class Durability:
    """Handles item wear and tear."""

    def __init__(
        self, max_wear: int = 0, current: int = 0, break_chance: float = 0.0
    ):
        self.max_wear = max_wear
        self.current = current
        self.break_chance = break_chance

    @property
    def has_wear(self) -> bool:
        return self.max_wear > 0

    @property
    def is_broken(self) -> bool:
        if not self.has_wear:
            return False
        return self.current >= self.max_wear

    @property
    def ratio(self) -> float:
        if not self.has_wear:
            return 0.0
        return min(max(self.current / self.max_wear, 0.0), 1.0)

    def increase(self, amount: int = 1) -> bool:
        """Increases wear and returns True if the item just broke."""
        if not self.has_wear:
            return False

        self.current = min(self.current + amount, self.max_wear)

        if self.is_broken or self.should_break():
            self.current = self.max_wear
            return True
        return False

    def try_increase(self, amount: int = 1) -> bool:
        if not self.has_wear or amount < 0:
            return False
        return self.increase(amount)

    def should_break(self) -> bool:
        if not self.has_wear:
            return False
        return random.random() < self.break_chance

    def reset(self) -> None:
        self.current = 0

    def try_reset(self) -> None:
        if self.has_wear:
            self.reset()

    def repair(self, amount: int = -1) -> None:
        if amount == -1:
            self.reset()
        else:
            self.current = max(0, self.current - amount)

    def try_repair(self, amount: int = -1) -> None:
        if not self.has_wear:
            return
        self.repair(amount)
