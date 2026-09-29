# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.session import Session
    from tuxemon.status.status import Status
    from tuxemon.technique.technique import Technique


class ActiveEffectManager:
    """
    Manages the lifecycle and update of all active techniques, items, and statuses
    that have ongoing, time-based effects.
    """

    def __init__(self) -> None:
        self.active_techniques: list[Technique] = []
        self.active_items: list[Item] = []
        self.active_statuses: list[Status] = []

    def update(self, session: Session, time_delta: float) -> None:
        """
        Updates all active effects and removes those that have finished.

        Parameters:
            session: The local game session (needed for effect handler updates).
            time_delta: Amount of time passed since last frame.
        """

        for tech in list(self.active_techniques):
            tech.effect_handler.update(session, time_delta)
            if tech.effect_handler.is_finished():
                self.active_techniques.remove(tech)

        for item in list(self.active_items):
            item.effect_handler.update(session, time_delta)
            if item.effect_handler.is_finished():
                self.active_items.remove(item)

        for status in list(self.active_statuses):
            status.effect_handler.update(session, time_delta)
            if status.effect_handler.is_finished():
                self.active_statuses.remove(status)

    def add_technique(self, tech: Technique) -> None:
        """Adds a technique to the active list."""
        self.active_techniques.append(tech)

    def add_item(self, item: Item) -> None:
        """Adds an item to the active list."""
        self.active_items.append(item)

    def add_status(self, status: Status) -> None:
        """Adds a status to the active list."""
        self.active_statuses.append(status)
