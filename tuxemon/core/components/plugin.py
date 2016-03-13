#!/usr/bin/python
# -*- coding: utf-8 -*-
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
# core.components.plugin Plugin architecture module.
#
#

import importlib
import inspect
import logging
import os
import sys

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)
log_hdlr = logging.StreamHandler(sys.stdout)
log_hdlr.setLevel(logging.DEBUG)
log_hdlr.setFormatter(logging.Formatter("%(asctime)s - %(name)s - "
                                        "%(levelname)s - %(message)s"))


class Plugin(object):
    def __init__(self, name, module):
        self.name = name
        self.plugin_object = module


class PluginManager(object):
    """Yapsy semi-compatible plugin manager.
    """

    def __init__(self, base_folders=None):
        if base_folders is None:
            base_folders = ["/data/data/org.tuxemon.game/files", "exe.win32-2.7", "tuxemon", "/mnt/Tuxemon"]
        self.folders = []
        self.base_folders = base_folders
        self.modules = []
        self.file_extension = ".plugin"
        self.exclude_classes = ["IPlugin"]
        self.include_patterns = ["core.components.event.actions", "core.components.event.conditions"]

    def setPluginPlaces(self, plugin_folders):
        self.folders = plugin_folders

    def collectPlugins(self):
        for folder in self.folders:
            folder = folder.replace('\\', '/')
            # Take the plugin folder and create a base module path based on it.
            for base_folder in self.base_folders:
                if base_folder in folder:
                    module_path = '.'.join(folder.split(base_folder + '/')[-1].split('/'))
                    break
            logger.debug("Plugin folder: " + folder)
            logger.debug("Module path: " + module_path)

            # Look for a ".plugin" in the plugin folder to create a list of modules
            # to import.
            modules = []
            for f in os.listdir(folder):
                if f.endswith(self.file_extension):
                    modules.append(module_path + "." + f.split(self.file_extension)[0])
            self.modules += modules
        logger.debug("Modules to load: " + str(self.modules))

    def getAllPlugins(self):
        imported_modules = []
        for module in self.modules:
            logger.debug("Importing module: " + str(module))
            m = importlib.import_module(module)
            for c in self._getClassesFromModule(m):
                class_name = c[0]
                class_obj = c[1]
                for pattern in self.include_patterns:
                    if class_name in self.exclude_classes:
                        continue
                    # Only import modules from the list of parent modules
                    if pattern in str(class_obj):
                        imported_modules.append(Plugin(module + "." + class_name, class_obj()))

        return imported_modules

    def _getClassesFromModule(self, module):
        members = inspect.getmembers(module, predicate=inspect.isclass)
        return members


def load_directory(plugin_folder):
    """Loads and imports a directory of plugins.

    :param plugin_folder: The folder to look for plugin files.
    :type plugin_folder: String

    :rtype: Dictionary
    :returns: A dictionary of imported plugins.

    """
    manager = PluginManager()
    manager.setPluginPlaces([plugin_folder])
    manager.collectPlugins()

    return manager


def get_available_methods(plugin_manager):
    """Gets the available methods in a dictionary of plugins.

    :param plugin_manager: A dictionary of modules.
    :type plugin_manager: yapsy.PluginManager

    :rtype: Dictionary
    :returns: A dictionary containing the methods from loaded plugins.

    **Example**

    >>> plugins = core.components.plugin.load_directory("core/components/menu")
    {'player_facing': <module 'player_facing' from 'core/components/event/player_facing.pyc'>}
    >>> core.components.plugin.get_available_methods(plugins)
    {'do_nothing': {'method': <function do_nothing at 0x7f20e1bec398>,
                    'module': 'player_facing'},
     'player_facing': {'method': <function player_facing at 0x7f20e1bec320>,
                       'module': 'player_facing'}}
    """
    methods = {}
    for plugin in plugin_manager.getAllPlugins():
        items = inspect.getmembers(plugin.plugin_object, predicate=inspect.ismethod)
        for method in items:
            methods[method[0]] = {"method": method[1], "module": plugin.name}

    return methods
