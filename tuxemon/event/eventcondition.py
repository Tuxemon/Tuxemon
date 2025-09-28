# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import ClassVar, Optional

from tuxemon.constants.paths import CONDITIONS_PATH, LIBDIR
from tuxemon.event import MapCondition
from tuxemon.plugin import load_plugins
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@dataclass
class EventCondition:
    name: ClassVar[str]
    is_expected: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        pass

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
            paths=[CONDITIONS_PATH],
            root_path=LIBDIR.parent,
            category="conditions",
            interface=EventCondition,
        )

    def get_condition(
        self, cond_data: MapCondition
    ) -> Optional[EventCondition]:
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
            condition_class = self.conditions[cond_data.type]
        except KeyError:
            logger.warning(
                f'EventCondition "{cond_data.type}" not implemented'
            )
            return None

        instance = condition_class()
        # Instantiate with parameters (positional unpacking)
        # try:
        #    instance = condition_class(*cond_data.parameters)
        # except TypeError as e:
        #    logger.error(f"Failed to instantiate {cond_data.type} with parameters {cond_data.parameters}: {e}")
        #    return None

        # Set expected state
        instance.is_expected = cond_data.operator == "is"
        return instance

    def get_conditions(self) -> list[type[EventCondition]]:
        """Return list of EventConditions."""
        return list(self.conditions.values())
