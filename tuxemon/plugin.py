# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import importlib
import inspect
import logging
import os
import sys
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


class PluginManager:
    """Yapsy semi-compatible plugin manager."""

    def __init__(self) -> None:
        self.folders: list[str] = []
        self.modules: list[str] = []
        self.file_extension = (".py", ".pyc")
        self.exclude_classes = ["IPlugin"]
        self.include_patterns = [
            "event.actions",
            "event.conditions",
            "item.effects",
            "item.conditions",
            "technique.effects",
            "technique.conditions",
            "condition.effects",
            "condition.conditions",
        ]

    def set_plugin_places(self, plugin_folders: Sequence[str]) -> None:
        """Set plugin search locations."""
        self.folders = list(plugin_folders)

    def collect_plugins(self) -> None:
        """Collect plugins from the specified folders."""
        for folder in self.folders:
            logger.debug(f"Searching for plugins: {folder}")
            if not os.path.exists(folder):
                logger.warning(f"Folder {folder} does not exist")
                continue

            folder = folder.replace("\\", "/")
            match = folder[folder.rfind("tuxemon") :]
            if not match:
                raise RuntimeError(
                    f"Unable to determine plugin module path for: {folder}"
                )

            module_path = match.replace("/", ".")
            for f in os.listdir(folder):
                if f.endswith(self.file_extension):
                    module_name = os.path.splitext(f)[0]
                    self.modules.append(f"{module_path}.{module_name}")

        logger.debug(f"Modules to load: {self.modules}")

    def get_all_plugins(
        self, *, interface: type[InterfaceValue]
    ) -> Sequence[Plugin[type[InterfaceValue]]]:
        """Get all loaded plugins implementing the given interface."""

        if not isinstance(interface, type):
            raise TypeError("interface must be a type")

        imported_modules: list[Plugin[type[InterfaceValue]]] = []
        for module_name in self.modules:
            logger.debug(f"Searching module: {module_name}")
            try:
                module = importlib.import_module(module_name)
            except ImportError as e:
                logger.error(f"Failed to import module {module_name}: {e}")
                continue

            for class_name, class_obj in self._get_classes_from_module(
                module, interface
            ):
                if class_name in self.exclude_classes:
                    logger.debug(f"Skipping {module_name}")
                    continue

                if any(
                    pattern in str(class_obj)
                    for pattern in self.include_patterns
                ):
                    logger.debug(f"Importing: {class_name}")
                    imported_modules.append(
                        Plugin(f"{module_name}.{class_name}", class_obj)
                    )

        return imported_modules

    def _get_classes_from_module(
        self, module: ModuleType, interface: type
    ) -> Iterable[tuple[str, type]]:
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
    manager = PluginManager()
    manager.set_plugin_places([plugin_folder])
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
