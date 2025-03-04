# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import MagicMock

from tuxemon.plugin import (
    PluginManager,
    PluginObject,
    get_available_classes,
    load_directory,
)


class TestPluginManager(unittest.TestCase):

    def test_init(self):
        manager = PluginManager()
        self.assertEqual(manager.folders, [])
        self.assertEqual(manager.modules, [])
        self.assertEqual(manager.FILE_EXTENSIONS, (".py", ".pyc"))
        self.assertEqual(manager.EXCLUDE_CLASSES, ["IPlugin"])
        self.assertEqual(
            manager.INCLUDE_PATTERNS,
            [
                "event.actions",
                "event.conditions",
                "item.effects",
                "item.conditions",
                "technique.effects",
                "technique.conditions",
                "condition.effects",
                "condition.conditions",
            ],
        )

    def test_set_plugin_places(self):
        manager = PluginManager()
        plugin_folders = ["folder1", "folder2"]
        manager.set_plugin_places(plugin_folders)
        self.assertEqual(manager.folders, plugin_folders)

    def test_collect_plugins(self):
        manager = PluginManager()
        manager.folders = ["folder1", "folder2"]
        manager.collect_plugins()
        # You can add assertions here based on the actual implementation of collect_plugins

    def test_get_all_plugins(self):
        manager = PluginManager()
        interface = PluginObject
        plugins = manager.get_all_plugins(interface=interface)
        self.assertIsInstance(plugins, list)

    def test_get_classes_from_module(self):
        manager = PluginManager()
        module = MagicMock()
        interface = PluginObject
        classes = manager._get_classes_from_module(module, interface)
        self.assertIsInstance(classes, list)

    def test_load_directory(self):
        plugin_folder = "folder1"
        loaded_manager = load_directory(plugin_folder)
        self.assertIsInstance(loaded_manager, PluginManager)

    def test_get_available_classes(self):
        manager = PluginManager()
        manager.set_plugin_places(["folder1"])
        manager.collect_plugins()
        interface = PluginObject
        classes = get_available_classes(manager, interface=interface)
        self.assertIsInstance(classes, list)
