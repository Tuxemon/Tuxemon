# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
"""Tests for tuxemon.save_system.map_autosave.MapAutosave."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock

from tuxemon.config import TuxemonConfig
from tuxemon.database.yaml_utils import dump_yaml_path
from tuxemon.save_system.map_autosave import MapAutosave


class TestMapAutosave:
    def test_first_update_never_saves(self):
        save = MagicMock()
        m = MapAutosave(save)
        assert m.update("world_1", can_save=True) is False
        save.assert_not_called()

    def test_map_change_can_save_saves_once_then_stops(self):
        save = MagicMock()
        m = MapAutosave(save)
        m.update("a", can_save=True)
        assert m.update("b", can_save=True) is True
        save.assert_called_once()
        # Further updates on the same map must not save again.
        assert m.update("b", can_save=True) is False
        assert m.update("b", can_save=True) is False
        save.assert_called_once()

    def test_blocked_change_sets_pending_then_later_unblocked_saves(self):
        save = MagicMock()
        m = MapAutosave(save)
        m.update("a", can_save=True)
        assert m.update("b", can_save=False) is False
        assert m.pending is True
        save.assert_not_called()
        assert m.update("b", can_save=True) is True
        assert m.pending is False
        save.assert_called_once()

    def test_two_blocked_changes_save_only_once_when_unblocked(self):
        save = MagicMock()
        m = MapAutosave(save)
        m.update("a", can_save=True)
        assert m.update("b", can_save=False) is False
        assert m.update("c", can_save=False) is False
        save.assert_not_called()
        assert m.update("c", can_save=True) is True
        save.assert_called_once()

    def test_empty_map_name_ignored(self):
        save = MagicMock()
        m = MapAutosave(save)
        assert m.update("", can_save=True) is False
        save.assert_not_called()
        # The empty name must not consume the "first map" slot,
        # so the next real name is still the starting map.
        assert m.update("a", can_save=True) is False
        save.assert_not_called()
        # A genuine map change from that point on saves.
        assert m.update("b", can_save=True) is True
        save.assert_called_once()

    def test_save_callback_raises_returns_false_pending_cleared(self):
        save = MagicMock(side_effect=RuntimeError("disk full"))
        m = MapAutosave(save)
        m.update("a", can_save=True)
        # update must not propagate the exception.
        assert m.update("b", can_save=True) is False
        assert m.pending is False
        save.assert_called_once()

    def test_settle_waits_for_safe_time_in_a_row(self):
        save = MagicMock()
        m = MapAutosave(save, settle=0.5)
        m.update("a", can_save=True, dt=0.1)
        assert m.update("b", can_save=True, dt=0.3) is False
        # An unsafe frame (gap between two scripted events) restarts the wait.
        assert m.update("b", can_save=False, dt=0.1) is False
        assert m.update("b", can_save=True, dt=0.3) is False
        save.assert_not_called()
        assert m.update("b", can_save=True, dt=0.3) is True
        save.assert_called_once()


class TestMapAutosaveSetting:
    def test_off_by_default(self):
        # World state only calls MapAutosave.update when this is True, so the
        # default means no autosave on a map change.
        cfg = TuxemonConfig(config_path=None)
        assert cfg.autosave_on_map_change is False

    def test_can_be_turned_on(self):
        with TemporaryDirectory() as td:
            path = Path(td) / "tuxemon.yaml"
            dump_yaml_path(
                path, {"gameplay": {"autosave_on_map_change": True}}
            )
            cfg = TuxemonConfig(config_path=path)
        assert cfg.autosave_on_map_change is True
