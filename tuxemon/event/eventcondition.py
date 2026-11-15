# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar

from tuxemon.constants.paths import (
    CONDITIONS_PATH,
    LIBDIR,
    get_plugin_paths,
)
from tuxemon.db import Operator, SpatialCondition
from tuxemon.plugin import PluginManager
from tuxemon.session import Session
from tuxemon.tools import cast_dataclass_parameters

logger = logging.getLogger(__name__)


@dataclass
class EventCondition:
    name: ClassVar[str]
    is_expected: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        cast_dataclass_parameters(self)

    def test(self, session: Session) -> bool:
        """Evaluate the condition and return True if it is satisfied."""
        return True


class ConditionManager:
    def __init__(self, root_path: Path | None = None) -> None:
        if root_path is None:
            root_path = LIBDIR.parent

        plugin_folders = get_plugin_paths(
            CONDITIONS_PATH, "conditions", subfolder="event"
        )

        manager = PluginManager.from_directory(
            plugin_folders=plugin_folders,
            root_path=root_path,
        )

        self.conditions: Mapping[str, type[EventCondition]] = (
            manager.get_class_map(interface=EventCondition)
        )

    def get_condition(
        self, cond_data: SpatialCondition
    ) -> EventCondition | None:
        """Instantiate a condition from map data, or return None if unavailable."""
        try:
            condition_class = self.conditions[cond_data.type]
        except KeyError:
            logger.warning(
                f'EventCondition "{cond_data.type}" not implemented'
            )
            return None

        try:
            instance = condition_class(*cond_data.parameters)
        except TypeError as e:
            logger.error(
                f"Failed to instantiate {cond_data.type} with parameters {cond_data.parameters}: {e}"
            )
            return None

        # Set expected state
        instance.is_expected = cond_data.operator == Operator.IS
        return instance

    def get_conditions(self) -> list[type[EventCondition]]:
        """Return list of EventConditions."""
        return list(self.conditions.values())
