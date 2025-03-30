# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar

from tuxemon.event import MapCondition
from tuxemon.session import Session


@dataclass
class EventCondition:
    name: ClassVar[str]

    def test(self, session: Session, condition: MapCondition) -> bool:
        """
        Return ``True`` if the condition is satisfied, or ``False`` if not.

        Parameters:
            session: Object containing the session information.
            condition: Condition defined in the map.

        Returns:
            Value of the condition.
        """
        return True

    def get_persist(self, session: Session) -> dict[str, Any]:
        """
        Return dictionary for this event class's data.
        This dictionary will track movement and be shared across all
        conditions. It will be saved when the game is saved.

        Returns:
            Dictionary with the persisting information.
        """
        try:
            return session.client.event_persist[self.name]
        except KeyError:
            persist: dict[str, Any] = {}
            session.client.event_persist[self.name] = persist
            return persist

    @property
    def done(self) -> bool:
        return True
