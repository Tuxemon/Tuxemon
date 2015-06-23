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
        pprint(items)
        for method in items:
            methods[method[0]] = {"method": method[1], "module": plugin.name}

    pprint(methods)
    return methods
