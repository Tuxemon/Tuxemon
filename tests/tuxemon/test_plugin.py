# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from collections.abc import Iterable
from unittest.mock import MagicMock, patch

from tuxemon.plugin import (
    DefaultPluginLoader,
    FileSystemPluginDiscovery,
    PluginManager,
    PluginObject,
    get_available_classes,
    load_directory,
)


class TestPluginManager(unittest.TestCase):
    def test_init(self):
        discovery = FileSystemPluginDiscovery([])
        loader = DefaultPluginLoader()
        manager = PluginManager(discovery, loader)
        self.assertEqual(manager.discovery.folders, [])
        self.assertEqual(manager.modules, [])

    def test_set_plugin_places(self):
        plugin_folders = ["folder1", "folder2"]
        discovery = FileSystemPluginDiscovery(plugin_folders)
        loader = DefaultPluginLoader()
        manager = PluginManager(discovery, loader)
        self.assertEqual(manager.discovery.folders, plugin_folders)

    def test_collect_plugins(self):
        plugin_folders = ["folder1", "folder2"]
        discovery = FileSystemPluginDiscovery(plugin_folders)
        loader = DefaultPluginLoader()
        manager = PluginManager(discovery, loader)
        manager.collect_plugins()

    def test_get_all_plugins(self):
        discovery = FileSystemPluginDiscovery([])
        loader = DefaultPluginLoader()
        manager = PluginManager(discovery, loader)
        interface = PluginObject
        plugins = manager.get_all_plugins(interface=interface)
        self.assertIsInstance(plugins, list)

    def test_get_classes_from_module(self):
        discovery = FileSystemPluginDiscovery([])
        loader = DefaultPluginLoader()
        manager = PluginManager(discovery, loader)
        module = MagicMock()
        interface = PluginObject
        classes = manager._get_classes_from_module(module, interface)
        self.assertIsInstance(classes, Iterable)

    def test_load_directory(self):
        plugin_folder = "folder1"
        loaded_manager = load_directory(plugin_folder)
        self.assertIsInstance(loaded_manager, PluginManager)

    def test_get_available_classes(self):
        plugin_folder = "folder1"
        manager = load_directory(plugin_folder)
        interface = PluginObject
        classes = get_available_classes(manager, interface=interface)
        self.assertIsInstance(classes, list)

    def test_file_system_plugin_discovery(self):
        discovery = FileSystemPluginDiscovery([])
        self.assertEqual(discovery.folders, [])
        self.assertEqual(discovery.file_extensions, (".py", ".pyc"))

    def test_default_plugin_loader(self):
        loader = DefaultPluginLoader()
        module_name = "test_module"
        with patch("importlib.import_module") as mock_import_module:
            loader.load_plugin(module_name)
            mock_import_module.assert_called_once_with(module_name)
