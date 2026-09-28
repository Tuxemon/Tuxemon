# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock, patch

import pytest

from tuxemon.map.terrain import TerrainManager


@pytest.fixture
def map_manager():
    mgr = MagicMock()
    mgr.surface_map = {}
    return mgr


@pytest.fixture
def terrain(map_manager):
    return TerrainManager(map_manager)


def test_get_all_tile_properties_basic(terrain, map_manager):
    map_manager.surface_map = {
        (0, 0): {"grass": 1.0},
        (1, 1): {"water": 0.5},
        (2, 2): {"grass": 2.0},
    }

    result = terrain.get_all_tile_properties("grass")
    assert set(result) == {(0, 0), (2, 2)}


def test_get_all_tile_properties_no_matches(terrain, map_manager):
    map_manager.surface_map = {
        (0, 0): {"grass": 1.0},
        (1, 1): {"grass": 2.0},
    }

    assert terrain.get_all_tile_properties("lava") == []


def test_get_all_tile_properties_empty_map(terrain, map_manager):
    map_manager.surface_map = {}
    assert terrain.get_all_tile_properties("grass") == []


@patch("tuxemon.map.terrain.SURFACE_KEYS", ["grass", "water"])
def test_update_tile_property_updates_existing_labels(terrain, map_manager):
    map_manager.surface_map = {
        (0, 0): {"grass": 1.0},
        (1, 1): {"grass": 2.0, "water": 0.5},
    }

    terrain.update_tile_property("grass", 9.0)

    assert map_manager.surface_map[(0, 0)]["grass"] == 9.0
    assert map_manager.surface_map[(1, 1)]["grass"] == 9.0


@patch("tuxemon.map.terrain.SURFACE_KEYS", ["grass", "water"])
def test_update_tile_property_does_not_create_new_labels(terrain, map_manager):
    map_manager.surface_map = {
        (0, 0): {"grass": 1.0},
    }

    terrain.update_tile_property("water", 5.0)

    assert "water" not in map_manager.surface_map[(0, 0)]


@patch("tuxemon.map.terrain.SURFACE_KEYS", ["grass"])
def test_update_tile_property_invalid_label_ignored(terrain, map_manager):
    map_manager.surface_map = {
        (0, 0): {"grass": 1.0},
    }

    terrain.update_tile_property("lava", 5.0)

    assert map_manager.surface_map[(0, 0)]["grass"] == 1.0
    assert "lava" not in map_manager.surface_map[(0, 0)]


@patch("tuxemon.map.terrain.SURFACE_KEYS", ["grass"])
def test_update_tile_property_no_mutation_when_value_same(
    terrain, map_manager
):
    map_manager.surface_map = {
        (0, 0): {"grass": 3.0},
    }

    terrain.update_tile_property("grass", 3.0)
    assert map_manager.surface_map[(0, 0)] == {"grass": 3.0}


def test_all_tiles_modified_true(terrain, map_manager):
    map_manager.surface_map = {
        (0, 0): {"grass": 5.0},
        (1, 1): {"grass": 5.0},
    }

    assert terrain.all_tiles_modified("grass", 5.0) is True


def test_all_tiles_modified_false(terrain, map_manager):
    map_manager.surface_map = {
        (0, 0): {"grass": 5.0},
        (1, 1): {"grass": 3.0},
    }

    assert terrain.all_tiles_modified("grass", 5.0) is False


def test_all_tiles_modified_no_tiles(terrain, map_manager):
    map_manager.surface_map = {
        (0, 0): {"water": 1.0},
    }

    assert terrain.all_tiles_modified("grass", 5.0) is True


def test_all_tiles_modified_missing_key_on_some_tiles(terrain, map_manager):
    map_manager.surface_map = {
        (0, 0): {"grass": 5.0},
        (1, 1): {"grass": 5.0, "water": 1.0},
        (2, 2): {"water": 1.0},  # does not contain "grass"
    }

    assert terrain.all_tiles_modified("grass", 5.0) is True
