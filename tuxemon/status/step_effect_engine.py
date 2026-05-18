# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from typing import TYPE_CHECKING

from tuxemon.db import StepEffectType

if TYPE_CHECKING:
    from tuxemon.monster.monster import Monster


class StepEffectEngine:
    """
    Handles step-based ticking and HP change calculations for a status.
    """

    def __init__(
        self,
        interval: int = 0,
        effect_type: StepEffectType | None = None,
        value: float = 0.0,
        initial_steps: float = 0.0,
    ) -> None:
        self.interval = interval
        self.effect_type = effect_type or StepEffectType.NONE
        self.value = value
        self.steps = initial_steps

    def add_steps(self, amount: float) -> int:
        """
        Add steps and return how many intervals were crossed.
        """
        if self.interval <= 0:
            return 0

        old_steps = self.steps
        self.steps += amount
        new_steps = self.steps

        old_intervals = old_steps // self.interval
        new_intervals = new_steps // self.interval

        ticks = int(new_intervals - old_intervals)

        if new_steps % self.interval == 0 and new_steps >= self.interval * 2:
            ticks -= 1

        return max(0, ticks)

    def compute_hp_change(self, monster: Monster, ticks: int) -> int:
        """
        Compute total HP change for the given number of ticks.
        """
        if self.effect_type == StepEffectType.NONE or self.value == 0.0:
            return 0

        v = self.value
        hp_change_per_tick = 0.0

        if self.effect_type == StepEffectType.FLAT_DAMAGE:
            hp_change_per_tick = -v

        elif self.effect_type == StepEffectType.PERCENT_MAX_HP_DAMAGE:
            hp_change_per_tick = -(monster.hp * (v / 100))

        elif self.effect_type == StepEffectType.PERCENT_CURRENT_HP_DAMAGE:
            hp_change_per_tick = -(monster.current_hp * (v / 100))

        elif self.effect_type == StepEffectType.PERCENT_MAX_HP_HEAL:
            hp_change_per_tick = monster.hp * (v / 100)

        elif self.effect_type == StepEffectType.PERCENT_CURRENT_HP_HEAL:
            hp_change_per_tick = monster.current_hp * (v / 100)

        return round(hp_change_per_tick * ticks)
