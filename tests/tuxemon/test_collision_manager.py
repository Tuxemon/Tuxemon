# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock

import pytest

from tuxemon.entity.entity import Entity
from tuxemon.map.collision_manager import CollisionManager
from tuxemon.map.manager import MapManager
from tuxemon.map.region import RegionProperties


@pytest.fixture
def map_manager():
    mm = MagicMock(spec=MapManager)
    mm.collision_map = {}
    mm.surface_map = {}
    return mm


@pytest.fixture
def collision_manager(map_manager):
    return CollisionManager(map_manager)


@pytest.fixture
def entity():
    e = MagicMock(spec=Entity)
    e.tile_pos = (1, 1)
    return e


# --- check_collision_zones ---


def test_check_collision_zones_returns_matching_coords(collision_manager):
    collision_map = {
        (0, 0): RegionProperties(key="warp"),
        (1, 1): RegionProperties(key="slide"),
        (2, 2): RegionProperties(key="warp"),
    }
    result = collision_manager.check_collision_zones(collision_map, "warp")
    assert set(result) == {(0, 0), (2, 2)}


def test_check_collision_zones_no_match(collision_manager):
    collision_map = {(0, 0): RegionProperties(key="slide")}
    result = collision_manager.check_collision_zones(collision_map, "warp")
    assert result == []


def test_check_collision_zones_skips_none_props(collision_manager):
    collision_map = {(0, 0): None, (1, 1): RegionProperties(key="warp")}
    result = collision_manager.check_collision_zones(collision_map, "warp")
    assert result == [(1, 1)]


# --- add_collision / remove_collision ---


def test_add_collision_registers_entity(collision_manager, entity):
    collision_manager.add_collision(entity, (1, 1))
    assert collision_manager.is_tile_occupied((1, 1))


def test_add_collision_overwrites_existing(collision_manager, entity):
    other = MagicMock(spec=Entity)
    collision_manager.add_collision(other, (1, 1))
    collision_manager.add_collision(entity, (1, 1))
    assert collision_manager.get_entity_at((1, 1)) is entity


def test_remove_collision_unregisters_entity(collision_manager, entity):
    collision_manager.add_collision(entity, (1, 1))
    collision_manager.remove_collision((1, 1))
    assert not collision_manager.is_tile_occupied((1, 1))


def test_remove_collision_on_empty_tile_is_safe(collision_manager):
    collision_manager.remove_collision((5, 5))  # should not raise


def test_remove_collision_does_not_affect_other_tiles(
    collision_manager, entity
):
    other = MagicMock(spec=Entity)
    collision_manager.add_collision(entity, (1, 1))
    collision_manager.add_collision(other, (2, 2))
    collision_manager.remove_collision((1, 1))
    assert collision_manager.is_tile_occupied((2, 2))


# --- is_tile_occupied / get_entity_at ---


def test_is_tile_occupied_false_when_empty(collision_manager):
    assert not collision_manager.is_tile_occupied((0, 0))


def test_is_tile_occupied_true_after_add(collision_manager, entity):
    collision_manager.add_collision(entity, (0, 0))
    assert collision_manager.is_tile_occupied((0, 0))


def test_get_entity_at_returns_none_when_empty(collision_manager):
    assert collision_manager.get_entity_at((0, 0)) is None


def test_get_entity_at_returns_correct_entity(collision_manager, entity):
    collision_manager.add_collision(entity, (3, 3))
    assert collision_manager.get_entity_at((3, 3)) is entity


# --- get_collision_map ---


def test_get_collision_map_includes_static_tiles(
    collision_manager, map_manager
):
    region = RegionProperties(key="warp")
    map_manager.collision_map = {(0, 0): region}
    result = collision_manager.get_collision_map()
    assert (0, 0) in result
    assert result[(0, 0)] is region


def test_get_collision_map_surface_impassable_added(
    collision_manager, map_manager
):
    map_manager.surface_map = {(1, 1): {"water": "0.0"}}
    result = collision_manager.get_collision_map()
    assert (1, 1) in result
    assert result[(1, 1)].key == "water"


def test_get_collision_map_surface_passable_excluded(
    collision_manager, map_manager
):
    map_manager.surface_map = {(1, 1): {"grass": "1.0"}}
    result = collision_manager.get_collision_map()
    assert (1, 1) not in result


def test_get_collision_map_entity_on_empty_tile_is_none(
    collision_manager, entity, map_manager
):
    collision_manager.add_collision(entity, (2, 2))
    result = collision_manager.get_collision_map()
    assert (2, 2) in result
    assert result[(2, 2)] is None


def test_get_collision_map_entity_on_terrain_tile_preserved(
    collision_manager, entity, map_manager
):
    region = RegionProperties(key="slide")
    map_manager.collision_map = {(2, 2): region}
    collision_manager.add_collision(entity, (2, 2))
    result = collision_manager.get_collision_map()
    # terrain data is preserved; entity blocking is handled via is_tile_occupied
    assert result[(2, 2)] is region


def test_get_collision_map_static_overwrites_surface(
    collision_manager, map_manager
):
    region = RegionProperties(key="warp")
    map_manager.surface_map = {(0, 0): {"water": "0.0"}}
    map_manager.collision_map = {(0, 0): region}
    result = collision_manager.get_collision_map()
    assert result[(0, 0)] is region
