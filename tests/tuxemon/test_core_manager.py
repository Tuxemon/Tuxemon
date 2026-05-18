# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tuxemon.core.core_manager import (
    ConditionManager,
    CoreManager,
    EffectManager,
)
from tuxemon.db import LogicCondition, ParameterizableRule
from tuxemon.plugin import PluginObject


@pytest.fixture
def temp_dir():
    d = Path(tempfile.mkdtemp())
    yield d
    for item in d.iterdir():
        if item.is_dir():
            item.rmdir()
    d.rmdir()


@pytest.fixture(autouse=True)
def no_mod_paths(monkeypatch):
    monkeypatch.setattr(
        "tuxemon.constants.paths.get_active_mod_paths", lambda: []
    )


@pytest.fixture(autouse=True)
def fake_mods_folder(monkeypatch, temp_dir):
    fake_mods = temp_dir / "mods"
    fake_mods.mkdir(exist_ok=True)
    monkeypatch.setattr("tuxemon.core.core_manager.mods_folder", fake_mods)


@pytest.fixture
def core_manager(temp_dir):
    path = temp_dir / "tuxemon"
    plugin_interface = MagicMock(spec=PluginObject)
    manager = CoreManager(
        plugin_interface, path, "category", "tuxemon", temp_dir.parent
    )
    manager.plugin_interface = plugin_interface
    manager.path = path
    return manager


@pytest.fixture
def effect_manager(temp_dir):
    path = temp_dir / "tuxemon"
    effect_class = MagicMock(spec=PluginObject)
    return EffectManager(
        effect_class,
        path,
        "tuxemon",
        root_path=temp_dir.parent,
    )


@pytest.fixture
def condition_manager(temp_dir):
    path = temp_dir / "tuxemon"
    condition_class = MagicMock(spec=PluginObject)
    return ConditionManager(
        condition_class,
        path,
        "tuxemon",
        root_path=temp_dir.parent,
    )


# CoreManager tests
@patch("tuxemon.plugin.PluginManager.from_directory")
def test_load_plugins(mock_from_directory, core_manager, temp_dir):
    fake_manager = MagicMock()
    fake_manager.get_class_map.return_value = {"TestPlugin": MagicMock()}
    mock_from_directory.return_value = fake_manager
    core_manager.load_plugins(
        core_manager.plugin_interface,
        core_manager.path,
        core_manager.category,
        temp_dir.parent,
    )
    assert "TestPlugin" in core_manager.classes


@patch("importlib.import_module")
def test_load_plugin_success(mock_import_module, core_manager):
    mock_module = MagicMock()
    mock_module.TestPlugin = MagicMock()
    mock_import_module.return_value = mock_module

    core_manager.load_plugin("TestPlugin")
    assert "TestPlugin" in core_manager.classes


@patch("importlib.import_module")
def test_load_plugin_failure(mock_import_module, core_manager, caplog):
    mock_import_module.side_effect = ImportError
    with caplog.at_level("ERROR", logger="tuxemon"):
        core_manager.load_plugin("NonExistentPlugin")
    assert "NonExistentPlugin" not in core_manager.classes


def test_unload_plugin_removes_sys_module(core_manager):
    fake_class = MagicMock()
    fake_class.__module__ = "tuxemon.category.testplugin"
    core_manager.classes["TestPlugin"] = fake_class
    sys.modules[fake_class.__module__] = MagicMock()

    core_manager.unload_plugin("TestPlugin")

    assert "TestPlugin" not in core_manager.classes
    assert fake_class.__module__ not in sys.modules


# Parametrized EffectManager tests
@pytest.mark.parametrize(
    "raw_effects, setup_classes, expect_empty",
    [
        pytest.param(
            [ParameterizableRule(type="effect_type", parameters=["param"])],
            {"effect_type": lambda: MagicMock(spec=PluginObject)},
            False,
            id="known_effect_type",
        ),
        pytest.param(
            [ParameterizableRule(type="unknown_type", parameters=["param"])],
            {},
            True,
            id="unknown_effect_type",
        ),
    ],
)
def test_parse_effects(
    effect_manager, raw_effects, setup_classes, expect_empty, caplog
):
    effect_manager.classes = {
        k: MagicMock(return_value=v()) for k, v in setup_classes.items()
    }
    with caplog.at_level("ERROR", logger="tuxemon"):
        parsed = effect_manager.parse_effects(raw_effects)
    if expect_empty:
        assert parsed == []
    else:
        assert any(isinstance(p, PluginObject) for p in parsed)


# Parametrized ConditionManager tests
@pytest.mark.parametrize(
    "raw_conditions, setup_classes, expect_empty",
    [
        pytest.param(
            [
                LogicCondition(
                    type="condition_type",
                    parameters=["param"],
                    operator="is",
                )
            ],
            {"condition_type": lambda: MagicMock(spec=PluginObject)},
            False,
            id="known_condition_type",
        ),
        pytest.param(
            [
                LogicCondition(
                    type="unknown_type",
                    parameters=["param"],
                    operator="is",
                )
            ],
            {},
            True,
            id="unknown_condition_type",
        ),
    ],
)
def test_parse_conditions(
    condition_manager, raw_conditions, setup_classes, expect_empty, caplog
):
    condition_manager.classes = {
        k: MagicMock(return_value=v()) for k, v in setup_classes.items()
    }
    with caplog.at_level("ERROR", logger="tuxemon"):
        parsed = condition_manager.parse_conditions(raw_conditions)
    if expect_empty:
        assert parsed == []
    else:
        assert any(isinstance(p, PluginObject) for p in parsed)


# CoreManager batch tests
@patch("importlib.import_module")
def test_load_plugins_batch_success_and_failure(
    mock_import_module, core_manager, caplog
):
    mock_module = MagicMock()
    mock_module.PluginA = MagicMock()
    mock_import_module.side_effect = [mock_module, ImportError]

    with caplog.at_level("ERROR", logger="tuxemon"):
        core_manager.load_plugins_batch(["PluginA", "NonExistentPlugin"])

    assert "PluginA" in core_manager.classes
    assert "NonExistentPlugin" not in core_manager.classes


def test_unload_plugins_batch(core_manager):
    fake_class_a = MagicMock()
    fake_class_a.__module__ = "tuxemon.category.plugina"
    fake_class_b = MagicMock()
    fake_class_b.__module__ = "tuxemon.category.pluginb"
    core_manager.classes["PluginA"] = fake_class_a
    core_manager.classes["PluginB"] = fake_class_b
    sys.modules[fake_class_a.__module__] = MagicMock()
    sys.modules[fake_class_b.__module__] = MagicMock()

    core_manager.unload_plugins_batch(["PluginA", "PluginB"])

    assert "PluginA" not in core_manager.classes
    assert "PluginB" not in core_manager.classes
    assert fake_class_a.__module__ not in sys.modules
    assert fake_class_b.__module__ not in sys.modules
