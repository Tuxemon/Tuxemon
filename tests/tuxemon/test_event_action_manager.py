# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock

import pytest

from tuxemon.event.eventaction import ActionManager


@pytest.fixture
def patch_action_plugins(monkeypatch):
    def _patch(mapping):
        fake_manager = MagicMock()
        fake_manager.get_class_map.return_value = mapping

        monkeypatch.setattr(
            "tuxemon.event.eventaction.PluginManager.from_directory",
            lambda *args, **kwargs: fake_manager,
        )

    return _patch


@pytest.fixture
def action_manager(patch_action_plugins):
    patch_action_plugins({})
    return ActionManager()


def test_init(patch_action_plugins):
    # Simulate some plugins being loaded
    patch_action_plugins({"foo": MagicMock()})
    mgr = ActionManager()
    assert len(mgr.actions) > 0


def test_get_action(patch_action_plugins):
    mock_action = MagicMock(return_value="add_monster")
    patch_action_plugins({"add_monster": mock_action})
    mgr = ActionManager()
    result = mgr.get_action("add_monster", ["monster_slug", 1])
    assert result is not None


def test_get_action_not_implemented(patch_action_plugins):
    patch_action_plugins({})
    mgr = ActionManager()
    result = mgr.get_action("action2")
    assert result is None


def test_get_action_with_type_error(patch_action_plugins):
    mock_action = MagicMock(side_effect=TypeError("Test error"))
    patch_action_plugins({"add_monster": mock_action})
    mgr = ActionManager()
    result = mgr.get_action("add_monster", ["param1", "param2"])
    assert result is None


def test_get_actions(patch_action_plugins):
    patch_action_plugins({"dummy": MagicMock()})
    mgr = ActionManager()
    actions = mgr.get_actions()
    assert len(actions) > 0
