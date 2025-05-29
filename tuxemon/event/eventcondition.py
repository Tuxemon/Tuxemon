# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import ClassVar, Optional

from tuxemon.constants.paths import CONDITIONS_PATH
from tuxemon.event import MapCondition
from tuxemon.plugin import load_plugins
from tuxemon.session import Session

logger = logging.getLogger(__name__)


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

    @property
    def done(self) -> bool:
        return True


class ConditionManager:
    def __init__(self) -> None:
        self.conditions = load_plugins(
            CONDITIONS_PATH.as_posix(),
            "conditions",
            interface=EventCondition,
        )

    def get_condition(self, name: str) -> Optional[EventCondition]:
        """
        Get a condition that is loaded into the engine.

        A new instance will be returned each time.

        Return ``None`` if condition is not loaded.

        Parameters:
            name: Name of the condition.

        Returns:
            New instance of the condition if that condition is loaded.
            ``None`` otherwise.
        """
        try:
            return self.conditions[name]()
        except KeyError:
            logger.warning(f'EventCondition "{name}" not implemented')
            return None

    def get_conditions(self) -> list[type[EventCondition]]:
        """Return list of EventConditions."""
        return list(self.conditions.values())
