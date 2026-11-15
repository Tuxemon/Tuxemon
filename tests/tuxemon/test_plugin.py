# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from collections.abc import Iterable
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tuxemon.constants.paths import LIBDIR
from tuxemon.plugin import (
    FileSystemPluginDiscovery,
    ImportLibPluginLoader,
    PluginFilter,
    PluginLoader,
    PluginManager,
    PluginObject,
)


@pytest.fixture
def discovery():
    return FileSystemPluginDiscovery([], LIBDIR)


@pytest.fixture
def loader():
    return PluginLoader(ImportLibPluginLoader())


@pytest.fixture
def plugin_filter():
    return PluginFilter()


@pytest.fixture
def manager(discovery, loader, plugin_filter):
    return PluginManager(discovery, loader, plugin_filter)


@pytest.fixture
def interface():
    return PluginObject


def test_init(manager):
    assert manager.discovery.folders == []
    assert manager.modules == []


@pytest.mark.parametrize(
    "folders",
    [
        pytest.param(["folder1"], id="one"),
        pytest.param(["folder1", "folder2"], id="two"),
        pytest.param([], id="none"),
    ],
)
def test_set_plugin_places(folders, loader, plugin_filter):
    discovery = FileSystemPluginDiscovery(folders, LIBDIR)
    manager = PluginManager(discovery, loader, plugin_filter)
    assert manager.discovery.folders == folders


def test_collect_plugins(plugin_filter, loader):
    discovery = FileSystemPluginDiscovery([Path("folder1")], LIBDIR)
    discovery.discover_plugin_files = MagicMock(
        return_value={
            "plugin1": Path("plugin1.py"),
            "plugin2": Path("plugin2.py"),
        }
    )

    manager = PluginManager(discovery, loader, plugin_filter)
    manager.collect_plugins()

    discovery.discover_plugin_files.assert_called_once()
    assert manager.modules == plugin_filter.filter_plugins(
        ["plugin1", "plugin2"]
    )


def test_collect_plugins_no_plugins_found(loader, plugin_filter):
    discovery = FileSystemPluginDiscovery([], LIBDIR)
    discovery.discover_plugins = MagicMock(return_value=[])

    manager = PluginManager(discovery, loader, plugin_filter)
    manager.collect_plugins()

    assert manager.modules == []


def test_get_all_plugins(manager, interface):
    plugins = manager.get_all_plugins(interface=interface)
    assert isinstance(plugins, list)


def test_scan_classes(manager, interface):
    module = MagicMock()
    classes = manager._scan_classes(module, interface)
    assert isinstance(classes, Iterable)


def test_load_directory():
    plugin_folder = Path("folder1")
    loaded_manager = PluginManager.from_directory([plugin_folder], LIBDIR)
    assert isinstance(loaded_manager, PluginManager)


def test_default_plugin_loader(loader):
    with patch("importlib.import_module") as mock_import:
        loader.load_plugin("test_module")
        mock_import.assert_called_once_with("test_module")


def test_default_plugin_loader_import_failure(loader):
    with patch(
        "importlib.import_module", side_effect=ImportError("Module not found")
    ):
        with pytest.raises(ImportError):
            loader.load_plugin("non_existent_module")


@pytest.mark.parametrize(
    "exclude, class_name, expected",
    [
        pytest.param(["Excluded"], "Excluded", True, id="excluded"),
        pytest.param(["Excluded"], "Other", False, id="other"),
        pytest.param([], "Anything", False, id="none"),
    ],
)
def test_plugin_filter_exclusion(exclude, class_name, expected):
    f = PluginFilter(exclude_classes=exclude)
    assert f.is_excluded(class_name) == expected


def test_plugin_filter_matches_patterns():
    f = PluginFilter(include_patterns=["Allowed"])

    class MockPlugin:
        pass

    assert not f.matches_patterns(MockPlugin)


def test_mock_plugin_manager(plugin_filter):
    discovery = MagicMock()
    loader = MagicMock()
    manager = PluginManager(discovery, loader, plugin_filter)

    discovery.discover_plugin_files.return_value = {
        "mock_plugin": Path("mock_plugin.py")
    }
    loader.load_plugin.return_value = MagicMock()

    manager.collect_plugins()
    discovery.discover_plugin_files.assert_called_once()

    assert manager.modules == plugin_filter.filter_plugins(["mock_plugin"])


def test_module_caching(manager):
    with patch.object(
        manager.loader, "load_plugin", return_value=MagicMock()
    ) as mock_load:
        manager.modules = ["pluginA"]
        manager.get_all_plugins(interface=PluginObject)
        manager.get_all_plugins(interface=PluginObject)
        mock_load.assert_called_once_with("pluginA")


def test_class_caching(manager):
    module = MagicMock()
    manager.modules = ["pluginA"]

    class Fake:
        name = "fake"

    with patch.object(manager.loader, "load_plugin", return_value=module):
        with patch.object(
            manager, "_scan_classes", return_value=[("Fake", Fake)]
        ) as mock_scan:
            manager.get_all_plugins(interface=PluginObject)
            manager.get_all_plugins(interface=PluginObject)

            mock_scan.assert_called_once()


def test_duplicate_class_suppression():
    class FakePlugin:
        name = "dup"

    plugins = {"dup": FakePlugin}

    existing_cls = plugins["dup"]
    new_cls = FakePlugin

    assert existing_cls is new_cls


def test_plugin_filter_matches_module_and_class():
    f = PluginFilter(include_patterns=["allowed"])

    class AllowedPlugin:
        __module__ = "tuxemon.allowed.plugins"
        __name__ = "AllowedPlugin"

    assert f.matches_patterns(AllowedPlugin)


def test_plugin_filter_rejects_non_matching():
    f = PluginFilter(include_patterns=["allowed"])

    class NotAllowed:
        __module__ = "tuxemon.other"
        __name__ = "Other"

    assert not f.matches_patterns(NotAllowed)


def test_real_plugin_loading(tmp_path):
    plugin_dir = tmp_path / "plugins"
    plugin_dir.mkdir()
    (plugin_dir / "__init__.py").write_text("")

    plugin_file = plugin_dir / "myplugin.py"

    plugin_code = """\
class MyPlugin:
    name = "myplugin"
"""

    plugin_file.write_text(plugin_code)

    import sys

    sys.path.insert(0, str(tmp_path))

    manager = PluginManager.from_directory(
        [plugin_dir], tmp_path, include=["myplugin"]
    )
    plugins = manager.get_all_plugins(interface=PluginObject)

    assert any(p.plugin_object.__name__ == "MyPlugin" for p in plugins)


def test_load_directory_initializes_manager(tmp_path):
    plugin_dir = tmp_path / "plugins"
    plugin_dir.mkdir()

    manager = PluginManager.from_directory([plugin_dir], tmp_path)

    assert isinstance(manager, PluginManager)
    assert manager.discovery.folders == [plugin_dir]


def test_get_classes_respects_interface(manager):
    class Base:
        pass

    class Child(Base):
        pass

    module = MagicMock()
    module.Child = Child
    module.Base = Base

    classes = manager._scan_classes(module, Base)
    names = [name for name, _ in classes]

    assert "Base" in names
    assert "Child" in names


def test_reload(manager):
    manager._loaded_modules = {"pluginA": MagicMock()}
    manager._class_cache = {("pluginA", PluginObject): [("Fake", MagicMock())]}

    with patch.object(manager, "collect_plugins") as mock_collect:
        manager.reload()

    assert manager._loaded_modules == {}
    assert manager._class_cache == {}
    mock_collect.assert_called_once()


def test_refresh_folders(manager):
    new_folders = [Path("new_folder")]

    with patch.object(manager.discovery, "set_folders") as mock_set:
        with patch.object(manager, "reload") as mock_reload:
            manager.refresh_folders(new_folders)

    mock_set.assert_called_once_with(new_folders)
    mock_reload.assert_called_once()


def test_reload_does_not_reload_modules(manager):
    manager._loaded_modules = {"pluginA": MagicMock()}

    with patch("importlib.reload") as mock_reload:
        with patch.object(manager, "collect_plugins"):
            manager.reload()

    mock_reload.assert_not_called()


def test_reload_preserves_modules(manager):
    manager.modules = ["pluginA", "pluginB"]

    with patch.object(manager, "collect_plugins"):
        manager.reload()

    assert manager.modules == ["pluginA", "pluginB"]
