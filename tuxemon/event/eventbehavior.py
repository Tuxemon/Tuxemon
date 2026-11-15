# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

from tuxemon.constants.paths import BEHAVS_PATH, LIBDIR, get_plugin_paths
from tuxemon.db import (
    Behavior,
    EventObject,
    ParameterizableRule,
    SpatialCondition,
)
from tuxemon.plugin import PluginManager

logger = logging.getLogger(__name__)


@dataclass
class EventBehavior(ABC):
    """
    Base interface for behavior plugins.

    A behavior converts a Behavior instance into real conditions and actions.
    """

    name: ClassVar[str]

    @abstractmethod
    def expand(
        self,
        event: EventObject,
        behavior: Behavior,
    ) -> tuple[list[SpatialCondition], list[ParameterizableRule]]: ...


class BehaviorManager:
    def __init__(self, root_path: Path | None = None) -> None:
        if root_path is None:
            root_path = LIBDIR.parent

        plugin_folders = get_plugin_paths(
            BEHAVS_PATH, "behaviors", subfolder="event"
        )

        manager = PluginManager.from_directory(
            plugin_folders=plugin_folders,
            root_path=root_path,
        )

        self.behaviors: Mapping[str, type[EventBehavior]] = (
            manager.get_class_map(interface=EventBehavior)
        )

    def get_behavior(self, name: str) -> EventBehavior | None:
        try:
            cls = self.behaviors[name]
        except KeyError:
            logger.warning(f'Behavior "{name}" not implemented')
            return None
        try:
            return cls()
        except Exception as e:
            logger.error(f"Error instantiating behavior {name}: {e}")
            return None

    def get_behaviors(self) -> list[type[EventBehavior]]:
        return list(self.behaviors.values())


def expand_behavior(
    event: EventObject, behavior_manager: BehaviorManager
) -> tuple[list[SpatialCondition], list[ParameterizableRule]]:
    """
    Expand all behaviors for an event in a single pass.
    Returns (all_conditions, all_actions) from a single expand() call per behavior.
    """
    all_conds: list[SpatialCondition] = []
    all_acts: list[ParameterizableRule] = []

    for beh in event.behavs:
        plugin = behavior_manager.get_behavior(beh.type)
        if not plugin:
            continue
        try:
            conds, acts = plugin.expand(event, beh)
            all_conds.extend(conds)
            all_acts.extend(acts)
        except Exception as e:
            logger.error(
                f"Behavior '{beh.type}' on event {event.id} failed to expand: {e}. "
                f"Skipping entire behavior."
            )

    return all_conds, all_acts
