# SPDX-License-Identifier: GPL-3.0
from unittest.mock import MagicMock

from tuxemon.npc_manager import NPCManager


def test_add_clients_to_map_does_not_clear_existing_npcs(monkeypatch) -> None:
    mgr = NPCManager()

    clear_mock = MagicMock()
    add_on_map_mock = MagicMock()
    add_off_map_mock = MagicMock()

    monkeypatch.setattr(mgr, "clear_npcs", clear_mock)
    monkeypatch.setattr(mgr, "add_npc", add_on_map_mock)
    monkeypatch.setattr(mgr, "add_npc_off_map", add_off_map_mock)

    sprite_same = MagicMock()
    sprite_other = MagicMock()

    registry = {
        "c1": {"sprite": sprite_same, "map_name": "map_a"},
        "c2": {"sprite": sprite_other, "map_name": "map_b"},
    }

    mgr.add_clients_to_map(registry, "map_a")

    clear_mock.assert_not_called()
    add_on_map_mock.assert_called_once_with(sprite_same)
    add_off_map_mock.assert_called_once_with(sprite_other)
