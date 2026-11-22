# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations


class Lifecycle:
    """
    Handles duration, stacking, and use-based expiration for a status.

    Turn counting is one-based. ``turn`` is the number of the round the
    status is currently on, not the number of rounds that have elapsed:

    - Gaining a status ticks it to 1 (``MonsterStatusHandler.apply_status``),
      so a freshly applied status is on turn 1.
    - Each round it survives ticks it again (``CombatSession.apply_statuses``).
    - Stacking (re-applying a status the monster already has) restarts it on
      turn 1, so a restacked status matches a fresh one.

    Code reading ``Status.nr_turn`` relies on this: ``NoddingOffEffect``
    gates on ``nr_turn > 1`` (not the round it was gained), and
    ``has_exceeded_duration`` uses ``turn > duration``, so a status with
    ``duration = N`` gets N full turns.

    Turns are only counted for statuses with a finite duration. When
    ``duration`` is 0 (endless), ``turn`` stays at 0 throughout: neither
    ticking nor stacking moves it. Effects that need to count rounds on an
    endless status should use ``use_counter`` instead.
    """

    def __init__(self, duration: int = 0, max_stacks: int = 5) -> None:
        self.duration = duration
        self.max_stacks = max_stacks

        self.turn: int = 0
        self.stack_level: int = 1
        self.use_counter: int = 0

    def tick_turn(self) -> None:
        """Advance the turn counter if the status has a finite duration."""
        if self.duration > 0:
            self.turn += 1

    def has_exceeded_duration(self) -> bool:
        """Returns True if the status has lasted longer than its duration."""
        return self.duration > 0 and self.turn > self.duration

    def advance_use(self) -> None:
        """Increment the use counter."""
        self.use_counter += 1

    def is_use_expired(self, max_uses: int = 1) -> bool:
        """Returns True if the status has been used too many times."""
        return self.use_counter >= max_uses

    def stack(self) -> tuple[int, int]:
        """
        Increase stack level up to max_stacks and refresh duration/uses.

        The turn counter restarts on turn 1, the same turn a freshly gained
        status starts on (see the class docstring). An endless status stays
        on 0, matching ``tick_turn``, which never counts its turns.
        """
        old = self.stack_level
        self.stack_level = min(self.stack_level + 1, self.max_stacks)

        self.turn = 1 if self.duration > 0 else 0
        self.use_counter = 0

        return old, self.stack_level
