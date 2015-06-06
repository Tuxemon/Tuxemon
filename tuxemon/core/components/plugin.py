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

import logging
import imp
import importlib
import os

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)

def get_plugins(plugin_folder):
    """Gets a list of available plugins in the specified directory.
        
    :param plugin_folder: The folder to look for .py plugin files.
    :type plugin_folder: String

    :rtype: List
    :returns: A list of dictionaries of the available plugins in the specified directory.

    **Example**

    >>> core.components.plugin.get_plugins("core/components/menu")
    [{'file': 'core/components/menu/item_menu.py',
      'name': 'item_menu',
      'path': 'core.components.menu.item_menu'},
     {'file': 'core/components/menu/main_menu.py',
      'name': 'main_menu',
      'path': 'core.components.menu.main_menu'},
     {'file': 'core/components/menu/bottom_menu.py',
      'name': 'bottom_menu',
      'path': 'core.components.menu.bottom_menu'},
     {'file': 'core/components/menu/monster_menu.py',
      'name': 'monster_menu',
      'path': 'core.components.menu.monster_menu'},
     {'file': 'core/components/menu/dialog_menu.py',
      'name': 'dialog_menu',
      'path': 'core.components.menu.dialog_menu'},
     {'file': 'core/components/menu/save_menu.py',
      'name': 'save_menu',
      'path': 'core.components.menu.save_menu'}]

    """

    plugins = []
    possible_plugins = os.listdir(plugin_folder)
    for file in possible_plugins:
        location = os.path.join(plugin_folder, file)
        location = location.replace("\\", "/")
        if not os.path.isfile(location):
            continue
        if "__init__" in file:
            continue
        if file.endswith(".py") or file.endswith(".pyo"):
            if file.endswith(".pyo"):
                location = location[:-1]
                file = file[:-1]
            plugins.append({"name": file[:-3],
                            "file": location,
                            "path": location.replace("/", ".")[:-3]})

    return plugins


def load_plugin(name, path):
    """Loads and imports a single plugin from a .py file.

    :param name: The name of the module to import.
    :param path: The file path to the .py file to import.

    :type name: String
    :type path: String

    :rtype: Module
    :returns: A module object of the plugin.

    **Example**

    >>> core.components.plugin.load_plugin("item_menu", "core/components/menu/item_menu.py")
    <module 'item_menu' from 'core/components/menu/item_menu.pyc'>

    """

    #return imp.load_source(name, path)
    path = path.replace("/", ".").split(".py")[0]
    return importlib.import_module(path)


def load_plugins(plugins):
    """Loads and imports all plugins from a list of dictionaries.

    :param plugins: A list of dictionaries of plugins to import.
    :type plugins: List

    :rtype: Dictionary
    :returns: A dictionary of imported plugins.

    **Example**

    >>> plugins = [{"name": "item_menu",
                    "file": "core/components/menu/item_menu.py"}]
    >>> core.components.plugin.load_plugins(plugins)
    {'item_menu': <module 'item_menu' from 'core/components/menu/item_menu.pyc'>}

    """
    all_plugins = {}
    for plugin in plugins:
        all_plugins[plugin["name"]] = load_plugin(plugin["name"], plugin["file"])

    return all_plugins


def load_directory(plugin_folder):
    """Loads and imports a directory of plugins.

    :param plugin_folder: The folder to look for .py plugin files.
    :type plugin_folder: String

    :rtype: Dictionary
    :returns: A dictionary of imported plugins.

    **Example**

    >>> core.components.plugin.load_directory("core/components/menu")
    {'bottom_menu': <module 'bottom_menu' from 'core/components/menu/bottom_menu.pyc'>,
     'dialog_menu': <module 'dialog_menu' from 'core/components/menu/dialog_menu.pyc'>,
     'item_menu': <module 'item_menu' from 'core/components/menu/item_menu.pyc'>,
     'main_menu': <module 'main_menu' from 'core/components/menu/main_menu.pyc'>,
     'monster_menu': <module 'monster_menu' from 'core/components/menu/monster_menu.pyc'>,
     'save_menu': <module 'save_menu' from 'core/components/menu/save_menu.pyc'>}
    """

    plugins = get_plugins(plugin_folder)
    return load_plugins(plugins)


def get_available_methods(plugins):
    """Gets the available methods in a dictionary of plugins.

    :param plugins: A dictionary of modules.
    :type plugins: Dictionary

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
    available_methods = {}
    for mod_name, mod in plugins.items():
        for function in dir(mod):
            if not function.startswith("__") and callable(getattr(mod, function)):
                available_methods[function] = {"module": mod_name,
                                               "method": getattr(mod, function)}

    return available_methods
