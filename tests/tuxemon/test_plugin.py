# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from collections.abc import Iterable
from unittest.mock import MagicMock, patch

from tuxemon.plugin import (
    FileSystemPluginDiscovery,
    ImportLibPluginLoader,
    PluginFilter,
    PluginLoader,
    PluginManager,
    PluginObject,
    get_available_classes,
    load_directory,
)


class TestPluginManager(unittest.TestCase):
    def setUp(self):
        self.discovery = FileSystemPluginDiscovery([])
        self.loader = PluginLoader(ImportLibPluginLoader())
        self.filter = PluginFilter()
        self.manager = PluginManager(self.discovery, self.loader, self.filter)
        self.interface = PluginObject

    def test_init(self):
        self.assertEqual(self.manager.discovery.folders, [])
        self.assertEqual(self.manager.modules, [])

    def test_set_plugin_places(self):
        plugin_folders = ["folder1", "folder2"]
        discovery = FileSystemPluginDiscovery(plugin_folders)
        manager = PluginManager(discovery, self.loader, self.filter)
        self.assertEqual(manager.discovery.folders, plugin_folders)

    def test_collect_plugins(self):
        plugin_folders = ["folder1", "folder2"]

        discovery = FileSystemPluginDiscovery(plugin_folders)
        discovery.discover_plugins = MagicMock(
            return_value=["plugin1", "plugin2"]
        )

        manager = PluginManager(discovery, self.loader, self.filter)
        manager.collect_plugins()

        discovery.discover_plugins.assert_called_once()

        filtered_plugins = self.filter.filter_plugins(["plugin1", "plugin2"])

        self.assertEqual(manager.modules, filtered_plugins)

    def test_get_all_plugins(self):
        plugins = self.manager.get_all_plugins(interface=self.interface)
        self.assertIsInstance(plugins, list)

    def test_get_classes_from_module(self):
        module = MagicMock()
        classes = self.manager._get_classes_from_module(module, self.interface)
        self.assertIsInstance(classes, Iterable)

    def test_load_directory(self):
        plugin_folder = "folder1"
        loaded_manager = load_directory(plugin_folder)
        self.assertIsInstance(loaded_manager, PluginManager)

    def test_get_available_classes(self):
        plugin_folder = "folder1"
        manager = load_directory(plugin_folder)
        classes = get_available_classes(manager, interface=self.interface)
        self.assertIsInstance(classes, list)

    def test_file_system_plugin_discovery(self):
        self.assertEqual(self.discovery.folders, [])
        self.assertEqual(self.discovery.file_extensions, (".py", ".pyc"))

    def test_default_plugin_loader(self):
        module_name = "test_module"
        with patch("importlib.import_module") as mock_import_module:
            self.loader.load_plugin(module_name)
            mock_import_module.assert_called_once_with(module_name)

    def test_plugin_filter(self):
        filter = PluginFilter(
            exclude_classes=["ExcludedPlugin"],
            include_patterns=["AllowedPattern"],
        )

        self.assertTrue(filter.is_excluded("ExcludedPlugin"))
        self.assertFalse(filter.is_excluded("SomeOtherPlugin"))

        class MockPlugin:
            pass

        self.assertFalse(filter.matches_patterns(MockPlugin))

    def test_default_plugin_loader_import_failure(self):
        module_name = "non_existent_module"
        with patch(
            "importlib.import_module",
            side_effect=ImportError("Module not found"),
        ):
            with self.assertRaises(ImportError):
                self.loader.load_plugin(module_name)

    def test_collect_plugins_no_plugins_found(self):
        discovery = FileSystemPluginDiscovery([])
        discovery.discover_plugins = MagicMock(return_value=[])

        manager = PluginManager(discovery, self.loader, self.filter)
        manager.collect_plugins()

        self.assertEqual(manager.modules, [])

    def test_mock_discover_plugins(self):
        discovery = FileSystemPluginDiscovery([])
        discovery.discover_plugins = MagicMock(
            return_value=["mock_plugin1", "mock_plugin2"]
        )

        self.assertEqual(
            discovery.discover_plugins(), ["mock_plugin1", "mock_plugin2"]
        )
        discovery.discover_plugins.assert_called_once()

    def test_mock_plugin_loader(self):
        mock_module = MagicMock()

        with patch(
            "importlib.import_module", return_value=mock_module
        ) as mock_import:
            module = self.loader.load_plugin("mock_plugin")

            self.assertEqual(module, mock_module)
            mock_import.assert_called_once_with("mock_plugin")

    def test_mock_plugin_manager(self):
        discovery = MagicMock()
        loader = MagicMock()
        filter = PluginFilter()
        manager = PluginManager(discovery, loader, filter)

        discovery.discover_plugins.return_value = ["mock_plugin"]
        loader.load_plugin.return_value = MagicMock()

        manager.collect_plugins()
        discovery.discover_plugins.assert_called_once()

        filtered_plugins = self.filter.filter_plugins(["mock_plugin"])

        self.assertEqual(manager.modules, filtered_plugins)
        discovery.discover_plugins.assert_called_once()

    def test_plugin_filter_exclusion(self):
        filter = PluginFilter(exclude_classes=["ExcludedPlugin"])

        self.assertTrue(filter.is_excluded("ExcludedPlugin"))
        self.assertFalse(filter.is_excluded("AllowedPlugin"))
