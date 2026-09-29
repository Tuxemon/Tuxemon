# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import importlib
import logging
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Generic, TypeVar

from tuxemon.constants.paths import (
    LIBDIR,
    get_plugin_paths,
    mods_folder,
)
from tuxemon.core.core_condition import CoreCondition
from tuxemon.core.core_effect import CoreEffect
from tuxemon.db import LogicCondition, Operator, ParameterizableRule
from tuxemon.plugin import PluginManager, PluginObject

logger = logging.getLogger(__name__)

LocalInterfaceValue = TypeVar("LocalInterfaceValue", bound=PluginObject)


class CoreManager(Generic[LocalInterfaceValue]):
    """Core class for managing the loading and unloading of plugins."""

    def __init__(
        self,
        interface: type[LocalInterfaceValue],
        path: Path,
        category: str,
        root_package_name: str,
        root_path: Path | None = None,
    ) -> None:
        self.category = category
        self.root_package_name = root_package_name
        self.classes: dict[str, type[LocalInterfaceValue]] = {}
        self.load_plugins(interface, path, category, root_path)

    def load_plugins(
        self,
        interface: type[LocalInterfaceValue],
        path: Path,
        category: str,
        root_path: Path | None,
    ) -> None:
        """Load all available plugins using the existing plugin system."""
        if root_path is None:
            root_path = LIBDIR.parent

        core_folders = get_plugin_paths(path, category, subfolder="core")

        mod_folders = get_plugin_paths(
            base_path=mods_folder,
            category=category,
            subfolder=None,
        )

        # Load core plugins
        core_manager = PluginManager.from_directory(
            plugin_folders=core_folders,
            root_path=root_path,
            include=[
                f.stem
                for folder in core_folders
                for f in folder.glob("*.py")
                if f.stem != "__init__"
            ],
        )
        core_plugins = core_manager.get_class_map(interface=interface)

        # Load mod plugins
        mod_manager = PluginManager.from_directory(
            plugin_folders=mod_folders,
            root_path=root_path,
            include=[
                f.stem
                for folder in mod_folders
                for f in folder.glob("*.py")
                if f.stem != "__init__"
            ],
        )
        mod_plugins = mod_manager.get_class_map(interface=interface)

        self.classes.update(core_plugins)
        self.classes.update(mod_plugins)

    def load_plugin(self, name: str) -> None:
        """Dynamically load a specific plugin by name."""
        if name in self.classes:
            logger.info(f"{self.category} '{name}' is already loaded.")
            return

        module_name = (
            f"{self.root_package_name}.{self.category}.{name.lower()}"
        )
        try:
            module = importlib.import_module(module_name)
            plugin_class = getattr(module, name)
            self.classes[name] = plugin_class

            logger.info(f"Successfully loaded {self.category}: {name}")
        except (ImportError, AttributeError) as e:
            logger.error(
                f"Failed to load {self.category} '{name}' from module {module_name}: {e}"
            )

    def unload_plugin(self, name: str) -> None:
        """Unload a specific plugin by name, including removal from sys.modules."""
        if name in self.classes:
            plugin_class = self.classes[name]
            module_name = plugin_class.__module__
            del self.classes[name]

            if module_name in sys.modules:
                del sys.modules[module_name]
                logger.debug(f"Removed module {module_name} from sys.modules.")

            logger.info(f"Unloaded {self.category}: {name}")

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


class EffectManager(CoreManager[CoreEffect]):
    """Manages the loading and unloading of item effects."""

    def __init__(
        self,
        effect_class: type[CoreEffect],
        path: Path,
        root_package_name: str,
        category: str = "effects",
        root_path: Path | None = None,
    ) -> None:
        """Initialize the EffectManager with the specific effect type."""
        super().__init__(
            effect_class, path, category, root_package_name, root_path
        )
        self.effect_class = effect_class

    def parse_effects(
        self, raw: Sequence[ParameterizableRule]
    ) -> Sequence[CoreEffect]:
        """Convert raw effect data into the specified effect objects."""
        effects: list[CoreEffect] = []
        for effect in raw:
            try:
                effect_class = self.classes[effect.type]
            except KeyError:
                logger.error(f'Effect type "{effect.type}" not implemented')
                continue
            else:
                effects.append(effect_class(*effect.parameters))
        return effects


class ConditionManager(CoreManager[CoreCondition]):
    """Manages the loading and unloading of various condition types."""

    def __init__(
        self,
        condition_class: type[CoreCondition],
        path: Path,
        root_package_name: str,
        category: str = "conditions",
        root_path: Path | None = None,
    ) -> None:
        """Initialize the ConditionManager with the specific condition type."""
        super().__init__(
            condition_class, path, category, root_package_name, root_path
        )
        self.condition_class = condition_class

    def parse_conditions(
        self, raw: Sequence[LogicCondition]
    ) -> Sequence[CoreCondition]:
        """Convert raw condition data into the specified condition objects."""
        conditions: list[CoreCondition] = []
        for condition in raw:
            try:
                condition_class = self.classes[condition.type]
            except KeyError:
                logger.error(
                    f'Condition type "{condition.type}" not implemented'
                )
                continue

            condition_obj = condition_class(*condition.parameters)

            if hasattr(condition_obj, "is_expected"):
                condition_obj.is_expected = condition.operator == Operator.IS

            conditions.append(condition_obj)

        return conditions
