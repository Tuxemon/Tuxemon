# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import importlib
import logging
from collections.abc import Sequence

from tuxemon import plugin
from tuxemon.db import CommonCondition, CommonEffect
from tuxemon.plugin import PluginObject

logger = logging.getLogger(__name__)


class CoreManager:
    """Core class for managing the loading and unloading of plugins."""

    def __init__(
        self, interface: type[PluginObject], path: str, category: str
    ) -> None:
        self.classes: dict[str, type[PluginObject]] = {}
        self.load_plugins(interface, path, category)

    def load_plugins(
        self, interface: type[PluginObject], path: str, category: str
    ) -> None:
        """Load all available plugins using the existing plugin system."""
        self.classes.update(
            plugin.load_plugins(path, category, interface=interface)
        )

    def load_plugin(self, name: str) -> None:
        """Dynamically load a specific plugin by name."""
        if name in self.classes:
            logger.info(
                f"{self.__class__.__name__} '{name}' is already loaded."
            )
            return

        module_name = f"{self.__class__.__name__.lower()}s.{name}"
        try:
            module = importlib.import_module(module_name)
            plugin_class = getattr(module, name)
            self.classes[name] = plugin_class
            logger.info(
                f"Successfully loaded {self.__class__.__name__.lower()}: {name}"
            )
        except (ImportError, AttributeError) as e:
            logger.error(
                f"Failed to load {self.__class__.__name__.lower()} '{name}': {e}"
            )

    def unload_plugin(self, name: str) -> None:
        """Unload a specific plugin by name."""
        if name in self.classes:
            del self.classes[name]
            logger.info(f"Unloaded {self.__class__.__name__.lower()}: {name}")

    def load_plugins_batch(self, names: list[str]) -> None:
        """Batch load multiple plugins by their names."""
        for name in names:
            try:
                self.load_plugin(name)
            except Exception as e:
                logger.error(
                    f"Failed to load {self.__class__.__name__.lower()} '{name}': {e}"
                )

    def unload_plugins_batch(self, names: list[str]) -> None:
        """Batch unload multiple plugins by their names."""
        for name in names:
            self.unload_plugin(name)

    def parse_object_effect(
        self, raw: Sequence[CommonEffect]
    ) -> Sequence[PluginObject]:
        """Parse raw effect data into PluginObject effects."""
        effects = []
        for effect in raw:
            try:
                effect_class = self.classes[effect.type]
            except KeyError:
                logger.error(f'Effect type "{effect.type}" not implemented')
                continue
            else:
                effects.append(effect_class(*effect.parameters))
        return effects

    def parse_object_condition(
        self, raw: Sequence[CommonCondition]
    ) -> Sequence[PluginObject]:
        """Parse raw condition data into PluginObject conditions."""
        conditions = []
        for condition in raw:
            try:
                condition_class = self.classes[condition.type]
            except KeyError:
                logger.error(
                    f'Condition type "{condition.type}" not implemented'
                )
                continue

            condition_obj = condition_class(*condition.parameters)
            if hasattr(condition_obj, "_op"):
                condition_obj._op = condition.operator == "is"
            conditions.append(condition_obj)

        return conditions


class EffectManager(CoreManager):
    """Manages the loading and unloading of item effects."""

    def __init__(
        self,
        effect_class: type[PluginObject],
        path: str,
        category: str = "effects",
    ) -> None:
        """
        Initialize the EffectManager with the specific effect type.
        """
        super().__init__(effect_class, path, category)
        self.effect_class = effect_class

    def parse_effects(
        self, raw: Sequence[CommonEffect]
    ) -> Sequence[PluginObject]:
        """Convert raw effect data into the specified effect objects."""
        return self.parse_object_effect(raw)


class ConditionManager(CoreManager):
    """Manages the loading and unloading of various condition types."""

    def __init__(
        self,
        condition_class: type[PluginObject],
        path: str,
        category: str = "conditions",
    ) -> None:
        """
        Initialize the ConditionManager with the specific condition type.
        """
        super().__init__(condition_class, path, category)
        self.condition_class = condition_class

    def parse_conditions(
        self, raw: Sequence[CommonCondition]
    ) -> Sequence[PluginObject]:
        """Convert raw condition data into the specified condition objects."""
        return self.parse_object_condition(raw)
