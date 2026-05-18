# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from typing import NamedTuple

from tuxemon.event import get_event_bus

logger = logging.getLogger(__name__)


class AFKThreshold(NamedTuple):
    """Defines a single AFK state threshold."""

    level: str
    duration: float  # The time (in seconds) to trigger this level


class AFKManager:
    """Manages AFK thresholds and state tracking."""

    def __init__(self) -> None:
        self.current_idle_time: float = 0.0
        self.thresholds: list[AFKThreshold] = []
        self.threshold_map: dict[str, float] = {}
        self.active_levels: set[str] = set()
        self.event_bus = get_event_bus()
        self._next_threshold_index: int = 0

    def add_threshold(self, level: str, duration: float) -> None:
        """Dynamically adds a new AFK threshold."""
        if duration <= 0:
            logger.warning(
                f"Ignoring threshold '{level}' with non-positive duration: {duration}"
            )
            return

        if level in self.threshold_map:
            logger.warning(f"Threshold '{level}' already exists. Skipping.")
            return

        new_threshold = AFKThreshold(level, duration)
        self.thresholds.append(new_threshold)
        self.thresholds.sort(key=lambda t: t.duration)
        self.threshold_map[level] = duration
        logger.debug(f"Added AFK threshold: {level} at {duration}s")

    def remove_threshold(self, level: str) -> bool:
        """Removes a threshold by its level name."""
        if level not in self.threshold_map:
            return False

        self.thresholds = [t for t in self.thresholds if t.level != level]
        del self.threshold_map[level]
        logger.info(f"Removed AFK threshold: {level}")
        return True

    def modify_threshold(self, level: str, new_duration: float) -> bool:
        """Modifies the duration of an existing threshold."""
        if level not in self.threshold_map:
            return False

        for i, t in enumerate(self.thresholds):
            if t.level == level:
                self.thresholds[i] = AFKThreshold(level, new_duration)
                self.thresholds.sort(key=lambda t: t.duration)
                self.threshold_map[level] = new_duration
                logger.info(
                    f"Modified AFK threshold {level} to {new_duration}s"
                )
                self.active_levels.clear()
                self._next_threshold_index = 0
                return True
        return False

    def update(self, dt: float) -> str | None:
        """
        Increments idle time and returns the new highest active threshold level
        if the state has changed.
        """
        self.current_idle_time = max(0.0, self.current_idle_time + dt)

        new_active_levels: set[str] = self.active_levels.copy()

        for i in range(self._next_threshold_index, len(self.thresholds)):
            threshold = self.thresholds[i]

            if self.current_idle_time >= threshold.duration:
                new_active_levels.add(threshold.level)
                self._next_threshold_index = i + 1
            else:
                break

        if new_active_levels != self.active_levels:
            gained_levels = new_active_levels - self.active_levels
            self.active_levels = new_active_levels

            if gained_levels:
                highest = max(
                    gained_levels,
                    key=lambda level: self.threshold_map[level],
                )
                self.event_bus.publish("afk.threshold_reached", level=highest)
                return highest

        return None

    def reset(self) -> str | None:
        """
        Resets idle time and active state. Returns the HIGHEST level the player was
        previously at, signaling a return to 'Active'.
        """
        if self.active_levels:
            highest_old_level = max(
                self.active_levels,
                key=lambda level: self.get_duration_by_level(level),
            )
            self.current_idle_time = 0.0
            self.active_levels.clear()
            self._next_threshold_index = 0

            logger.info(
                f"Player returned to active from level: {highest_old_level}"
            )
            self.event_bus.publish("afk.reset", from_level=highest_old_level)
            return highest_old_level

        self.current_idle_time = 0.0
        self._next_threshold_index = 0
        return None

    @property
    def current_level(self) -> str | None:
        """Returns the current highest active AFK level name."""
        if not self.active_levels:
            return None
        return max(
            self.active_levels,
            key=lambda level: self.get_duration_by_level(level),
        )

    def is_threshold_met(self, level_name: str) -> bool:
        """Returns True if the specified AFK level (or any higher level) is currently active."""
        return level_name in self.active_levels

    def get_duration_by_level(self, level_name: str) -> float:
        """Helper to look up a duration by level name."""
        return self.threshold_map.get(level_name, 0.0)
