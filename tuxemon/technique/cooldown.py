# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class Cooldown:
    """Handles cooldown logic for techniques, items, or statuses."""

    def __init__(self, duration: int = 0):
        if duration < 0:
            raise ValueError("Cooldown duration cannot be negative")

        self.duration = duration
        self.remaining = 0
        self.frozen_turns = 0
        self.haste_turns = 0
        self.shield = False
        self.charge = 0
        self.locked = False
        self.delay_turns = 0
        self.multiplier = 1.0
        self.min_remaining = 0

    @property
    def is_recharging(self) -> bool:
        return self.remaining > 0

    @property
    def is_ready(self) -> bool:
        return self.remaining == 0

    def add(self, amount: int, max_value: int) -> None:
        if amount < 0:
            logger.error("Cooldown.add() does not accept negative values")
            return
        if self.locked:
            return
        self.remaining = min(self.remaining + amount, max_value)

    def trigger(self) -> None:
        if self.shield:
            self.shield = False
            return
        if self.locked:
            return
        # delay means cooldown does not start immediately
        if self.delay_turns > 0:
            self.remaining = 0
            return
        self.remaining = self.duration

    def tick(self, amount: int = 1, *, paused: bool = False) -> None:
        if paused:
            return

        if amount < 0:
            logger.error("Cooldown.tick() does not accept negative values")
            return

        if self.locked:
            return

        # delay phase
        if self.delay_turns > 0:
            self.delay_turns -= 1
            return

        # freeze
        if self.frozen_turns > 0:
            self.frozen_turns -= 1
            return

        # haste
        if self.haste_turns > 0:
            self.remaining = max(
                self.min_remaining, self.remaining - amount * 2
            )
            self.haste_turns -= 1
            return

        # multiplier (generalized haste/slow)
        if self.multiplier != 1.0:
            self.remaining = max(
                self.min_remaining,
                self.remaining - int(amount * self.multiplier),
            )
            return

        # normal tick
        self.remaining = max(self.min_remaining, self.remaining - amount)

    def reset(self) -> None:
        if not self.locked:
            self.remaining = 0
            self.delay_turns = 0
            self.frozen_turns = 0
            self.haste_turns = 0
            self.charge = 0

    def swap_with(self, other: Cooldown) -> None:
        if self.locked or other.locked:
            return

        self.__dict__, other.__dict__ = (
            other.__dict__.copy(),
            self.__dict__.copy(),
        )
