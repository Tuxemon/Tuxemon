# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import importlib
import importlib.util
import inspect
import logging
import sys
from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import (
    ClassVar,
    Generic,
    Protocol,
    TypeVar,
    runtime_checkable,
)

from tuxemon.constants.paths import (
    PLUGIN_INCLUDE_PATTERNS,
)

logger = logging.getLogger(__name__)
log_hdlr = logging.StreamHandler(sys.stdout)
log_hdlr.setLevel(logging.DEBUG)
log_hdlr.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
)


@runtime_checkable
class PluginObject(Protocol):
    name: ClassVar[str]


T = TypeVar("T")
InterfaceValue = TypeVar("InterfaceValue", bound=PluginObject)


@dataclass(frozen=True)
class Plugin(Generic[T]):
    name: str
    plugin_object: T
    origin: Path


class PluginDiscovery(ABC):
    """
    Responsible for discovering plugins in a given folder.
    """

    @abstractmethod
    def discover_plugins(self) -> list[str]:
        """Discovers plugin modules."""

    @abstractmethod
    def discover_plugin_files(self) -> dict[str, Path]:
        """Return module_name → file_path mapping."""

    @abstractmethod
    def set_folders(self, folders: list[Path]) -> None:
        """Sets the folders to search for plugins."""


class FileSystemPluginDiscovery(PluginDiscovery):
    def __init__(
        self,
        folders: list[Path],
        root_path: Path,
        file_extensions: tuple[str, str] = (".py", ".pyc"),
    ):
        self.folders = folders or []
        self.root_path = root_path.resolve()
        self.file_extensions = file_extensions

    def discover_plugins(self) -> list[str]:
        return list(self.discover_plugin_files().keys())

    def discover_plugin_files(self) -> dict[str, Path]:
        """Return a mapping of module_name → file_path."""
        modules: dict[str, Path] = {}
        for folder in self.folders:
            folder_path = folder
            if not folder_path.exists():
                logger.warning(f"Folder {folder_path} does not exist")
                continue

            module_path = self._get_module_path(folder_path)

            for file in folder_path.iterdir():
                if file.suffix in self.file_extensions and file.is_file():
                    module_name = f"{module_path}.{file.stem}"
                    modules[module_name] = file.resolve()

        return modules

    def set_folders(self, folders: list[Path]) -> None:
        """Sets the folders to search for plugins."""
        self.folders = folders

    def _get_module_path(self, folder: Path) -> str:
        """Converts a folder path to a module path using pathlib."""
        folder = folder.resolve()
        try:
            relative = folder.relative_to(self.root_path)
        except ValueError:
            raise RuntimeError(
                f"{folder} is not under root path {self.root_path}"
            )
        return ".".join(relative.parts)


class PluginLoader:
    """
    Responsible for loading plugins from a module.
    """

    def __init__(self, strategy: PluginLoadingStrategy) -> None:
        self.strategy = strategy

    def load_plugin(self, module_name: str) -> ModuleType:
        """Loads a plugin module."""
        return self.strategy.load_plugin(module_name)


class PluginLoadingStrategy(ABC):
    @abstractmethod
    def load_plugin(self, module_name: str) -> ModuleType:
        """Loads a plugin module."""


class ImportLibPluginLoader(PluginLoadingStrategy):
    def load_plugin(self, module_name: str) -> ModuleType:
        try:
            return importlib.import_module(module_name)
        except ImportError as e:
            logger.error(f"Failed to import module {module_name}: {e}")
            raise


class ImportLibFileLoader(PluginLoadingStrategy):
    def load_plugin(self, module_path: str) -> ModuleType:
        spec = importlib.util.spec_from_file_location("plugin", module_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load module from {module_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


class PluginFilter:
    def __init__(
        self,
        exclude_classes: list[str] = ["IPlugin"],
        include_patterns: list[str] = PLUGIN_INCLUDE_PATTERNS,
    ) -> None:
        self.exclude_classes_set = set(exclude_classes)
        self.include_patterns_set = set(include_patterns)

    def is_excluded(self, class_name: str) -> bool:
        """Check if a class should be excluded based on its simple name."""
        return class_name in self.exclude_classes_set

    def matches_pattern(self, string: str) -> bool:
        """Check if a string matches any of the inclusion patterns."""
        return any(pattern in string for pattern in self.include_patterns_set)

    def matches_patterns(self, class_obj: type) -> bool:
        """
        Check if a class matches inclusion patterns using introspection
        on its module path and name.
        """
        module_path = class_obj.__module__
        class_name = class_obj.__name__

        # Check if the inclusion patterns match the full module path OR the class name
        # Example: pattern 'plugins' matches module 'tuxemon.plugins.game'
        # Example: pattern 'Command' matches class 'LoadCommand'
        return self.matches_pattern(module_path) or self.matches_pattern(
            class_name
        )

    def filter_plugins(self, module_names: list[str]) -> list[str]:
        """Filters plugin modules based on patterns (using module path)."""
        return [
            module for module in module_names if self.matches_pattern(module)
        ]

    def is_valid_plugin(self, class_name: str, class_obj: type) -> bool:
        """Check if a plugin should be included by checking exclusion and inclusion."""
        if self.is_excluded(class_name):
            logger.debug(
                f"Skipping class '{class_name}' because it's in the exclusion list."
            )
            return False

        if not self.matches_patterns(class_obj):
            logger.debug(
                f"Skipping class '{class_name}' because its module path or name does not match an include pattern."
            )
            return False

        return True


class PluginManager:
    """
    Central manager for discovering, loading, caching, and reloading plugins.
    """

    def __init__(
        self,
        discovery: PluginDiscovery,
        loader: PluginLoader,
        filter: PluginFilter | None,
    ) -> None:
        self.discovery = discovery
        self.loader = loader
        self.filter = filter or PluginFilter()
        self.modules: list[str] = []
        self._origins: dict[str, Path] = {}
        self._loaded_modules: dict[str, ModuleType] = {}
        self._class_cache: dict[tuple[str, type], list[tuple[str, type]]] = {}

    @classmethod
    def from_directory(
        cls,
        plugin_folders: list[Path],
        root_path: Path,
        exclude: list[str] = ["IPlugin"],
        include: list[str] | None = None,
    ) -> PluginManager:
        discovery = FileSystemPluginDiscovery(plugin_folders, root_path)
        loader = PluginLoader(ImportLibPluginLoader())
        filter = PluginFilter(
            exclude_classes=exclude,
            include_patterns=include or PLUGIN_INCLUDE_PATTERNS,
        )

        manager = cls(discovery, loader, filter)
        manager.collect_plugins()
        return manager

    def collect_plugins(self) -> None:
        """
        Discover plugin modules and update internal module lists.
        """
        logger.debug("Discovering plugins...")
        module_map = self.discovery.discover_plugin_files()

        filtered = self.filter.filter_plugins(list(module_map.keys()))
        self.modules = list(dict.fromkeys(filtered))
        self._origins = {m: module_map[m] for m in self.modules}

        logger.debug(f"Modules discovered: {self.modules}")

    def _load_module(self, module_name: str) -> ModuleType | None:
        """
        Load a module using the configured loader, with error handling.
        """
        try:
            module = self.loader.load_plugin(module_name)
            self._loaded_modules[module_name] = module
            return module
        except ImportError as e:
            logger.error(
                f"Skipping module '{module_name}' due to import error: {e}"
            )
            return None

    def get_all_plugins(
        self, *, interface: type[InterfaceValue]
    ) -> Sequence[Plugin[type[InterfaceValue]]]:
        """
        Return all plugin classes implementing the given interface.
        """
        imported_plugins: list[Plugin[type[InterfaceValue]]] = []

        for module_name in self.modules:
            module = self._loaded_modules.get(
                module_name
            ) or self._load_module(module_name)
            if module is None:
                continue

            imported_plugins.extend(
                self._get_plugins_from_module(module, module_name, interface)
            )

        return imported_plugins

    def _scan_classes(
        self, module: ModuleType, interface: type
    ) -> Iterable[tuple[str, type]]:
        """
        Extract all classes from a module that match the interface.
        """
        predicate = (
            inspect.isclass
            if interface is PluginObject
            else lambda c: inspect.isclass(c) and issubclass(c, interface)
        )
        return inspect.getmembers(module, predicate=predicate)

    def _get_plugins_from_module(
        self, module: ModuleType, module_name: str, interface: type
    ) -> list[Plugin[type[InterfaceValue]]]:

        cache_key = (module_name, interface)

        if cache_key not in self._class_cache:
            scanned = self._scan_classes(module, interface)
            filtered = [
                (name, cls)
                for name, cls in scanned
                if self.filter.is_valid_plugin(name, cls)
            ]
            self._class_cache[cache_key] = filtered

        return [
            Plugin(
                name=f"{module_name}.{class_name}",
                plugin_object=class_obj,
                origin=self._origins[module_name],
            )
            for class_name, class_obj in self._class_cache[cache_key]
        ]

    def reload(self) -> None:
        """
        Safely reload plugin discovery and class caches.
        Does NOT use importlib.reload() to avoid breaking module state.
        """
        logger.debug("Reloading plugins...")

        self._loaded_modules.clear()
        self._class_cache.clear()
        self.collect_plugins()

    def refresh_folders(self, folders: list[Path]) -> None:
        """
        Update plugin folders and reload everything.
        """
        self.discovery.set_folders(folders)
        self.reload()

    def get_class_map(
        self,
        interface: type[InterfaceValue] | type[PluginObject] = PluginObject,
    ) -> Mapping[str, type]:
        """
        Return a mapping of plugin keys → plugin classes.
        Includes:
        - fully qualified plugin name (module.Class)
        - short plugin name (cls.name), if present
        """
        classes: dict[str, type] = {}

        for plugin in self.get_all_plugins(interface=interface):
            cls = plugin.plugin_object

            fq_key = plugin.name
            short_key = getattr(cls, "name", None)

            if interface is PluginObject and short_key is None:
                logger.error(
                    f"Class {cls.__name__} ({fq_key}) does not have a required `name` attribute."
                )
                continue

            # Fully qualified key
            if fq_key not in classes:
                classes[fq_key] = cls
            else:
                logger.warning(
                    f"Duplicate fully qualified plugin key '{fq_key}'. Skipping."
                )

            # Short key
            if short_key:
                if short_key not in classes:
                    classes[short_key] = cls
                else:
                    existing_cls = classes[short_key]
                    if existing_cls is not cls:
                        logger.warning(
                            f"Duplicate short plugin key '{short_key}'. "
                            f"Existing: {existing_cls.__module__}.{existing_cls.__name__}, "
                            f"New: {cls.__module__}.{cls.__name__}. Keeping existing."
                        )

        return classes
