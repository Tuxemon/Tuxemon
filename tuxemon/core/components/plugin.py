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

from yapsy.PluginManager import PluginManager
from pprint import pformat, pprint
import logging
import os
import inspect
import importlib
import sys

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)
plugin_logger = logging.getLogger('yapsy')
plugin_logger.setLevel(logging.DEBUG)
log_hdlr = logging.StreamHandler(sys.stdout)
log_hdlr.setLevel(logging.DEBUG)
log_hdlr.setFormatter(logging.Formatter("%(asctime)s - %(name)s - "
                                        "%(levelname)s - %(message)s"))
plugin_logger.addHandler(log_hdlr)

class Plugin(object):
    def __init__(self, name, module):
        self.name = name
        self.plugin_object = module


class TuxPluginManager(object):
    """Yapsy semi-compatible plugin manager.
    """

    def __init__(self, base_folders=["files", "tuxemon"]):
        self.folders = []
        self.base_folders = base_folders
        self.modules = []
        self.file_extension = ".yapsy-plugin"
        self.exclude_classes = ["IPlugin"]

    def setPluginPlaces(self, plugin_folders):
        self.folders = plugin_folders

    def collectPlugins(self):
        for folder in self.folders:
            # Take the plugin folder and create a base module path based on it.
            for base_folder in self.base_folders:
                if base_folder in folder:
                    module_path = '.'.join(folder.split(base_folder + os.sep)[-1].split(os.sep))
                    break
            logger.debug("Plugin folder: " + folder)
            logger.debug("Module path: " + module_path)

            # Look for a "yapsy-plugin" in the plugin folder to create a list of modules
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
            print "Importing module:", module
            m = importlib.import_module(module)
            for c in self._getClassesFromModule(m):
                class_name = c[0]
                class_obj = c[1]
                if class_name not in self.exclude_classes:
                    imported_modules.append(Plugin(module + "." + class_name, class_obj()))

        return imported_modules


    def _getClassesFromModule(self, module):
        members = inspect.getmembers(module, predicate=inspect.isclass)
        return members


def manual_load_directory(plugin_folder):
    """Manually loads events instead of using a plugin manager. This is
    necessary for certain platforms such as Android, which doesn't
    provide an easy way to dynamically load plugins.
    """
    print "  Manual loading"
    import importlib

    # Take the plugin folder and create a base module path based on it.
    module_path = '.'.join(plugin_folder.split("tuxemon" + os.sep)[-1].split(os.sep))
    print "PLUGIN FOLDER:", plugin_folder
    print "MODULE PATH:", module_path

    # Look for a "yapsy-plugin" in the plugin folder to create a list of modules
    # to import.
    modules = []
    for f in os.listdir(plugin_folder):
        if f.endswith(".yapsy-plugin"):
            modules.append(f.split(".yapsy-plugin")[0])

    for module in modules:
        manual_get_methods(importlib.import_module(module_path + "." + module))

    #import core.components.event.actions.player as act_player
    #manual_get_methods(act_player.Player)

def manual_get_methods(module):
    for class_name, c in module.__dict__.items():
        if "__" not in class_name:
            if inspect.isclass(c) and class_name != "IPlugin":
                print "  Class name:", class_name
                for method_name, m in c.__dict__.items():
                    if "__" not in method_name:
                        print method_name

def load_directory(plugin_folder):
    """Loads and imports a directory of plugins.

    :param plugin_folder: The folder to look for plugin files.
    :type plugin_folder: String

    :rtype: Dictionary
    :returns: A dictionary of imported plugins.

    """
    #manual_load_directory(plugin_folder)
    #m = TuxPluginManager()
    #m.setPluginPlaces([plugin_folder])
    #m.collectPlugins()
    #print "MANAGER MODULES:", m.getAllPlugins()
    #methods = {}
    #for plugin in m.getAllPlugins():
    #    items = inspect.getmembers(plugin.plugin_object, predicate=inspect.ismethod)
    #    for method in items:
    #        methods[method[0]] = {"method": method[1], "module": plugin.name}
    #print methods

    manager = TuxPluginManager()
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
