# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock

import pytest

from tuxemon.map.transition import MapTransition


@pytest.fixture
def deps(mocker):
    """Provides all mocked dependencies for MapTransition."""
    return {
        "map_loader": mocker.MagicMock(),
        "npc_manager": mocker.MagicMock(),
        "map_manager": mocker.MagicMock(),
        "boundary": mocker.MagicMock(),
        "event_engine": mocker.MagicMock(),
    }


@pytest.fixture
def transition(deps):
    return MapTransition(
        deps["map_loader"],
        deps["npc_manager"],
        deps["map_manager"],
        deps["boundary"],
        deps["event_engine"],
    )


def test_init(deps, transition):
    assert transition.map_loader is deps["map_loader"]
    assert transition.map_manager is deps["map_manager"]
    assert transition.npc_manager is deps["npc_manager"]
    assert transition.boundary is deps["boundary"]
    assert transition.event_engine is deps["event_engine"]


def test_change_map(deps, transition):
    map_data = MagicMock()
    deps["map_loader"].load_map_data.return_value = map_data
    transition.change_map("test_map")
    deps["map_loader"].load_map_data.assert_called_once_with("test_map")
    deps["event_engine"].reset.assert_called_once_with(map_data)
    deps["map_manager"].load_map.assert_called_once_with(map_data)
    deps["npc_manager"].clear_npcs.assert_called_once()
    deps["boundary"].set_rectangular_boundary.assert_called_once()


@pytest.mark.parametrize(
    "size",
    [
        pytest.param((10, 10), id="size_10x10"),
        pytest.param((20, 15), id="size_20x15"),
        pytest.param((1, 1), id="size_1x1"),
    ],
)
def test_update_boundaries_parametrized(deps, transition, size):
    deps["map_manager"].map_size = size
    transition._update_boundaries()
    deps["boundary"].set_rectangular_boundary.assert_called_once_with(
        "map", 0, size[0], 0, size[1]
    )


def test_reset_events(deps, transition):
    map_data = MagicMock()
    transition._reset_events(map_data)
    deps["event_engine"].reset.assert_called_once_with(map_data)


def test_update_map_state(deps, transition):
    map_data = MagicMock()
    transition._update_map_state(map_data)
    deps["map_manager"].load_map.assert_called_once_with(map_data)


def test_clear_npcs(deps, transition):
    transition._clear_npcs()
    deps["npc_manager"].clear_npcs.assert_called_once()


def test_change_map_order_of_operations(deps, transition):
    call_order = []
    map_data = MagicMock()
    deps["npc_manager"].clear_npcs.side_effect = lambda: call_order.append(
        "clear_npcs"
    )
    deps["map_loader"].load_map_data.side_effect = lambda name: (
        call_order.append("load_map") or map_data
    )
    transition.change_map("test_map")
    assert call_order == ["clear_npcs", "load_map"]


def test_change_map_loader_failure(deps, transition):
    deps["map_loader"].load_map_data.side_effect = Exception("Map load failed")
    with pytest.raises(Exception, match="Map load failed"):
        transition.change_map("broken_map")


def test_change_map_twice(deps, transition):
    map_data = MagicMock()
    deps["map_loader"].load_map_data.return_value = map_data
    transition.change_map("map_a")
    transition.change_map("map_a")
    assert deps["map_manager"].load_map.call_count == 2


def test_npc_collision_removed_from_old_map(deps, transition):
    mock_npc = MagicMock()
    mock_npc.remove_collision = MagicMock()
    deps["map_manager"].map_size = (10, 10)
    deps["map_loader"].load_map_data.return_value = MagicMock()
    deps["npc_manager"].get_all_entities.return_value = [mock_npc]

    def clear_npcs_side_effect():
        for npc in deps["npc_manager"].get_all_entities():
            npc.remove_collision()

    deps["npc_manager"].clear_npcs.side_effect = clear_npcs_side_effect
    transition.change_map("new_map")
    mock_npc.remove_collision.assert_called_once()
