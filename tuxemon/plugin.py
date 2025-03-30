# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import importlib
import inspect
import logging
import os
import sys
from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping, Sequence
from types import ModuleType
from typing import (
    ClassVar,
    Generic,
    Protocol,
    TypeVar,
    Union,
    overload,
    runtime_checkable,
)

from tuxemon.constants.paths import PLUGIN_INCLUDE_PATTERNS

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
Interface = type[InterfaceValue]


class Plugin(Generic[T]):
    __slots__ = ("name", "plugin_object")

    def __init__(self, name: str, module: T) -> None:
        self.name = name
        self.plugin_object = module


class PluginDiscovery(ABC):
    """
    Responsible for discovering plugins in a given folder.
    """

    @abstractmethod
    def discover_plugins(self) -> list[str]:
        """Discovers plugin modules."""

    @abstractmethod
    def set_folders(self, folders: list[str]) -> None:
        """Sets the folders to search for plugins."""


class PluginLoader(ABC):
    """
    Responsible for loading plugins from a module.
    """

    @abstractmethod
    def load_plugin(self, module_name: str) -> ModuleType:
        """Loads a plugin module."""


class FileSystemPluginDiscovery(PluginDiscovery):
    FOLDER = "tuxemon"
    FILE_EXTENSIONS = (".py", ".pyc")

    def __init__(
        self,
        folders: list[str],
        file_extensions: tuple[str, str] = FILE_EXTENSIONS,
    ):
        self.folders = folders if folders else []
        self.file_extensions = file_extensions

    def discover_plugins(self) -> list[str]:
        """Discovers plugin modules from the file system."""
        modules = []
        for folder in self.folders:
            if not os.path.exists(folder):
                logger.warning(f"Folder {folder} does not exist")
                continue

            module_path = self._get_module_path(folder)
            for file_name in os.listdir(folder):
                if file_name.endswith(self.file_extensions):
                    module_name = os.path.splitext(file_name)[0]
                    modules.append(f"{module_path}.{module_name}")
        return modules

    def set_folders(self, folders: list[str]) -> None:
        """Sets the folders to search for plugins."""
        self.folders = folders

    def _get_module_path(self, folder: str) -> str:
        """Converts a folder path to a module path."""
        folder = folder.replace("\\", "/")
        match = folder[folder.rfind(self.FOLDER) :]
        if not match:
            raise RuntimeError(
                f"Unable to determine plugin module path for: {folder}"
            )
        return match.replace("/", ".")


class DefaultPluginLoader(PluginLoader):
    def load_plugin(self, module_name: str) -> ModuleType:
        """Loads a plugin module using importlib."""
        try:
            return importlib.import_module(module_name)
        except ImportError as e:
            logger.error(f"Failed to import module {module_name}: {e}")
            raise


class PluginManager:
    """Yapsy semi-compatible plugin manager."""

    EXCLUDE_CLASSES = ["IPlugin"]
    INCLUDE_PATTERNS = PLUGIN_INCLUDE_PATTERNS

    def __init__(
        self, discovery: PluginDiscovery, loader: PluginLoader
    ) -> None:
        self.discovery = discovery
        self.loader = loader
        self.modules: list[str] = []

    def collect_plugins(self) -> None:
        """Collect plugins from the specified folders."""
        logger.debug("Discovering plugins...")
        self.modules = self.discovery.discover_plugins()
        logger.debug(f"Modules to load: {self.modules}")

    def get_all_plugins(
        self, *, interface: type[InterfaceValue]
    ) -> Sequence[Plugin[type[InterfaceValue]]]:
        """Get all loaded plugins implementing the given interface."""
        imported_plugins: list[Plugin[type[InterfaceValue]]] = []
        for module_name in self.modules:
            module = self.loader.load_plugin(module_name)
            imported_plugins.extend(
                self._get_plugins_from_module(module, module_name, interface)
            )
        return imported_plugins

    def _get_plugins_from_module(
        self, module: ModuleType, module_name: str, interface: type
    ) -> list[Plugin[type[InterfaceValue]]]:
        """
        Retrieves plugins from a given module, filtering by a specific interface
        and inclusion patterns.
        """
        plugins: list[Plugin[type[InterfaceValue]]] = []
        for class_name, class_obj in self._get_classes_from_module(
            module, interface
        ):
            if class_name in self.EXCLUDE_CLASSES:
                logger.debug(f"Skipping {module_name}.{class_name}")
                continue

            if any(
                pattern in str(class_obj) for pattern in self.INCLUDE_PATTERNS
            ):
                logger.debug(f"Importing: {module_name}.{class_name}")
                plugins.append(
                    Plugin(f"{module_name}.{class_name}", class_obj)
                )
        return plugins

    def _get_classes_from_module(
        self, module: ModuleType, interface: type
    ) -> Iterable[tuple[str, type]]:
        """Retrieves classes from a module that match a given interface."""
        # This is required because of
        # https://github.com/python/typing/issues/822
        #
        # The typing error in issubclass will be solved
        # in https://github.com/python/typeshed/pull/5658
        predicate = (
            inspect.isclass
            if interface is PluginObject
            else lambda c: inspect.isclass(c) and issubclass(c, interface)
        )
        return inspect.getmembers(module, predicate=predicate)


def load_directory(plugin_folder: str) -> PluginManager:
    """
    Load plugins from a directory.

    Parameters:
        plugin_folder: The folder where to look for plugin files.

    Returns:
        A plugin manager, with the modules already loaded.
    """
    discovery = FileSystemPluginDiscovery([plugin_folder])
    loader = DefaultPluginLoader()
    manager = PluginManager(discovery, loader)
    manager.collect_plugins()
    return manager


def get_available_classes(
    plugin_manager: PluginManager, *, interface: type[InterfaceValue]
) -> Sequence[type[InterfaceValue]]:
    """
    Get available classes from a plugin manager.

    Parameter:
        plugin_manager: Plugin manager with modules already loaded.
        interface: Superclass or protocol of the returned classes.

    Returns:
        Sequence of loaded classes.
    """
    return [
        plugin.plugin_object
        for plugin in plugin_manager.get_all_plugins(interface=interface)
    ]


# Overloads until https://github.com/python/mypy/issues/3737 is fixed


@overload
def load_plugins(
    path: str, category: str = "plugins"
) -> Mapping[str, type[PluginObject]]:
    pass


@overload
def load_plugins(
    path: str, category: str = "plugins", *, interface: type[InterfaceValue]
) -> Mapping[str, type[InterfaceValue]]:
    pass


def load_plugins(
    path: str,
    category: str = "plugins",
    *,
    interface: Union[type[InterfaceValue], type[PluginObject]] = PluginObject,
) -> Mapping[str, Union[type[InterfaceValue], type[PluginObject]]]:
    """
    Load plugins from a directory and return them by name.

    Parameters:
        path: Location of the modules to load.
        category: Optional string for debugging info.
        interface: Superclass or protocol of the returned classes. If no
            class is given, they are only required to have a `name` attribute.

    Returns:
        A dictionary mapping the `name` attribute of each class to the class
        itself.
    """
    classes: dict[str, Union[type[InterfaceValue], type[PluginObject]]] = {}
    plugins = load_directory(path)

    for cls in get_available_classes(plugins, interface=interface):
        try:
            name = cls.name
        except AttributeError:
            logger.error(
                f"Class {cls.__name__} does not have a `name` attribute"
            )
            continue
        classes[name] = cls
        logger.info(f"loaded {category}: {cls.name}")

    return classes
