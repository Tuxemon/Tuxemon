#
# Tuxemon
# Copyright (C) 2014, William Edwards <shadowapex@gmail.com>,
#                     Benjamin Bean <superman2k5@gmail.com>
#
# This file is part of Tuxemon.
#
# Tuxemon is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Tuxemon is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Tuxemon.  If not, see <http://www.gnu.org/licenses/>.
#
# Contributor(s):
#
# William Edwards <shadowapex@gmail.com>
#
#
# plugin Plugin architecture module.
#
#

from __future__ import annotations
import importlib
import inspect
import logging
import os
import re
import sys
from typing import (
    Mapping, Sequence, Any, Optional, List, Iterable,
    Protocol, Tuple, Type, TypeVar, Generic, overload, Union,
    ClassVar, runtime_checkable
)
from types import ModuleType

logger = logging.getLogger(__name__)
log_hdlr = logging.StreamHandler(sys.stdout)
log_hdlr.setLevel(logging.DEBUG)
log_hdlr.setFormatter(
    logging.Formatter(
        "%(asctime)s - %(name)s - " "%(levelname)s - %(message)s",
    ),
)


@runtime_checkable
class PluginObject(Protocol):
    name: ClassVar[str]


T = TypeVar("T")
InterfaceValue = TypeVar("InterfaceValue", bound=PluginObject)
Interface = Type[InterfaceValue]


class Plugin(Generic[T]):
    __slots__ = ("name", "plugin_object")

    def __init__(self, name: str, module: T) -> None:
        self.name = name
        self.plugin_object = module


class PluginManager:
    """Yapsy semi-compatible plugin manager."""

    def __init__(
        self,
    ) -> None:

        self.folders: Sequence[str] = []
        self.modules: List[str] = []
        self.file_extension = (".py", ".pyc")
        self.exclude_classes = ["IPlugin"]
        self.include_patterns = [
            "event.actions",
            "event.conditions",
            "item.effects",
            "item.conditions",
        ]

    def setPluginPlaces(self, plugin_folders: Sequence[str]) -> None:
        """
        Set the locations where to look for plugins.

        Parameters:
            plugin_folders: Sequence of folders that might contain plugins.

        """
        self.folders = plugin_folders

    def collectPlugins(self) -> None:
        """Collect the plugins from the folders."""
        for folder in self.folders:
            logger.debug("searching for plugins: %s", folder)
            folder = folder.replace("\\", "/")
            # Take the plugin folder and create a base module path based on it.
            pattern = re.compile("tuxemon/.*$")
            matches = pattern.findall(folder)
            if len(matches) == 0:
                logger.exception(
                    f"Unable to determine plugin module path for: %s",
                    folder,
                )
                raise RuntimeError
            module_path = matches[0].replace("/", ".")

            # Look for a ".plugin" in the plugin folder to create a list
            # of modules to import.
            modules = []
            for f in os.listdir(folder):
                if f.endswith(self.file_extension):
                    modules.append(module_path + "." + os.path.splitext(f)[0])
            self.modules += modules
        logger.debug("Modules to load: " + str(self.modules))

    def getAllPlugins(
        self,
        *,
        interface: Type[InterfaceValue],
    ) -> Sequence[Plugin[Type[InterfaceValue]]]:
        """
        Get a sequence of loaded plugins.

        Parameters:
            interface: Superclass or protocol of the returned classes.

        Returns:
            Sequence of plugins loaded.

        """
        imported_modules = []
        for module in self.modules:
            logger.debug("Searching module: " + str(module))
            m = importlib.import_module(module)
            for c in self._getClassesFromModule(m, interface=interface):
                class_name = c[0]
                class_obj = c[1]
                for pattern in self.include_patterns:
                    if class_name in self.exclude_classes:
                        logger.debug("Skipping " + str(module))
                        continue

                    # Only import modules from the list of parent modules
                    if pattern in str(class_obj):
                        logger.debug("Importing: " + str(class_name))
                        imported_modules.append(
                            Plugin(module + "." + class_name, class_obj),
                        )

        return imported_modules

    def _getClassesFromModule(
        self,
        module: ModuleType,
        interface: Type[InterfaceValue],
    ) -> Iterable[Tuple[str, Type[InterfaceValue]]]:

        # This is required because of
        # https://github.com/python/typing/issues/822
        #
        # The typing error in issubclass will be solved
        # in https://github.com/python/typeshed/pull/5658
        predicate = (
            inspect.isclass if interface is PluginObject
            else lambda c: inspect.isclass(c) and issubclass(c, interface)
        )

        members = inspect.getmembers(
            module,
            predicate=predicate
        )
        return members


def load_directory(plugin_folder: str) -> PluginManager:
    """
    Loads and imports a directory of plugins.

    Parameters:
        plugin_folder: The folder where to look for plugin files.

    Returns:
        A plugin manager, with the modules already loaded.

    """
    manager = PluginManager()
    manager.setPluginPlaces([plugin_folder])
    manager.collectPlugins()

    return manager


def get_available_classes(
    plugin_manager: PluginManager,
    *,
    interface: Type[InterfaceValue],
) -> Sequence[Type[InterfaceValue]]:
    """
    Gets the available classes in a plugin manager.

    Parameter:
        plugin_manager: Plugin manager with modules already loaded.
        interface: Superclass or protocol of the returned classes.

    Returns:
        Sequence of loaded classes.

    """
    classes = []
    for plugin in plugin_manager.getAllPlugins(interface=interface):
        classes.append(plugin.plugin_object)

    return classes


# Overloads until https://github.com/python/mypy/issues/3737 is fixed

@overload
def load_plugins(
    path: str,
    category: str = "plugins",
) -> Mapping[str, Type[PluginObject]]:
    pass


@overload
def load_plugins(
    path: str,
    category: str = "plugins",
    *,
    interface: Type[InterfaceValue]
) -> Mapping[str, Type[InterfaceValue]]:
    pass


def load_plugins(
    path: str,
    category: str = "plugins",
    *,
    interface: Union[Type[InterfaceValue], Type[PluginObject]] = PluginObject
) -> Mapping[str, Union[Type[InterfaceValue], Type[PluginObject]]]:
    """
    Load classes using plugin system.

    Parameters:
        path: Location of the modules to load.
        category: Optional string for debugging info.
        interface: Superclass or protocol of the returned classes. If no
            class is given, they are only required to have a `name` attribute.

    Returns:
        A dictionary mapping the `name` attribute of each class to the class
        itself.

    """
    classes = dict()
    plugins = load_directory(path)

    for cls in get_available_classes(plugins, interface=interface):
        name = getattr(cls, "name", None)
        if name is None:
            logger.error(f"found incomplete {category}: {cls.__name__}")
            continue
        classes[name] = cls
        logger.info(f"loaded {category}: {cls.name}")

    return classes
