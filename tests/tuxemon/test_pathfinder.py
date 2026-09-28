# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock

import pytest

from tuxemon.boundary import BoundaryChecker
from tuxemon.client import LocalPygameClient
from tuxemon.db import Direction
from tuxemon.map.collision_manager import CollisionManager
from tuxemon.map.manager import MapManager
from tuxemon.map.map import dirs2
from tuxemon.map.region import RegionProperties
from tuxemon.movement import Pathfinder
from tuxemon.npc_manager import NPCManager
from tuxemon.user_config import CONFIG


@pytest.fixture
def client():
    c = MagicMock(spec=LocalPygameClient)
    c.map_manager = MagicMock(spec=MapManager)
    c.map_manager.map_size = (10, 10)
    c.map_manager.collision_lines_map = {}
    c.boundary = MagicMock(spec=BoundaryChecker)
    c.npc_manager = MagicMock(spec=NPCManager)
    c.collision_manager = MagicMock(spec=CollisionManager)
    return c


@pytest.fixture
def pathfinder(client):
    return Pathfinder(
        client.npc_manager,
        client.map_manager,
        client.collision_manager,
        client.boundary,
    )


@pytest.mark.parametrize(
    "exits, expected",
    [
        pytest.param([], None, id="no_exits_none"),
        pytest.param([], None, id="no_exits_duplicate_case"),
    ],
)
def test_pathfind_no_exits(client, pathfinder, exits, expected):
    client.collision_manager.get_collision_map.return_value = {}
    client.npc_manager.get_entity_pos.return_value = None
    pathfinder.get_exits = MagicMock(return_value=exits)

    result = pathfinder.pathfind((0, 0), (1, 1), Direction.DOWN)

    assert result is expected


def test_pathfind_same_start_and_dest(client, pathfinder):
    client.collision_manager.get_collision_map.return_value = {}
    client.npc_manager.get_entity_pos.return_value = None

    result = pathfinder.pathfind((1, 1), (1, 1), Direction.DOWN)
    assert result == []


@pytest.mark.parametrize(
    "within_bounds, pos, skip_nodes, expected",
    [
        pytest.param(
            True, (1, 1), {(2, 2)}, True, id="valid_in_bounds_not_skipped"
        ),
        pytest.param(False, (1, 1), {(2, 2)}, False, id="out_of_bounds"),
        pytest.param(
            True, (2, 2), {(2, 2)}, False, id="position_in_skip_nodes"
        ),
    ],
)
def test_is_valid_position(
    client, pathfinder, within_bounds, pos, skip_nodes, expected
):
    client.boundary.is_within_boundaries.return_value = within_bounds
    assert pathfinder.is_valid_position(pos, skip_nodes) is expected


def test_is_tile_traversable_basic(client, pathfinder):
    tile = (1, 2)
    pathfinder.get_exits = MagicMock(return_value=[tile])
    client.npc_manager.get_entity_pos.return_value = None

    assert pathfinder.is_tile_traversable((1, 1), Direction.DOWN, tile, False)


def test_is_tile_traversable_blocked_by_npc(client, pathfinder):
    tile = (1, 2)
    pathfinder.get_exits = MagicMock(return_value=[tile])

    npc = MagicMock()
    npc.moving = True
    npc.moverate = CONFIG.player_walkrate
    npc.facing = Direction.UP

    client.npc_manager.get_entity_pos.return_value = npc

    assert not pathfinder.is_tile_traversable(
        (1, 1), Direction.DOWN, tile, False
    )


def test_is_tile_traversable_ignore_npc(client, pathfinder):
    tile = (1, 2)
    pathfinder.get_exits = MagicMock(return_value=[tile])
    client.npc_manager.get_entity_pos.return_value = MagicMock()

    assert pathfinder.is_tile_traversable((1, 1), Direction.DOWN, tile, True)


def test_get_exits_with_tile_data(client, pathfinder):
    client.collision_manager.is_tile_occupied.return_value = False
    position = (1, 1)
    collision_map = {
        position: RegionProperties([], ["down", "right"], [], None, None),
        (1, 2): RegionProperties(["up"], [], [], None, None),
        (2, 1): RegionProperties(["left"], ["up"], [], None, None),
    }

    client.collision_manager.get_collision_map.return_value = collision_map
    client.boundary.is_within_boundaries.return_value = True

    exits = pathfinder.get_exits(position, Direction.DOWN)
    assert exits == [(1, 2), (2, 1)]


def test_get_exits_no_valid_exits(client, pathfinder):
    position = (1, 1)
    collision_map = {position: MagicMock(endure=None, exit_from=[])}

    client.collision_manager.get_collision_map.return_value = collision_map
    client.boundary.is_within_boundaries.return_value = True

    exits = pathfinder.get_exits(position, Direction.DOWN)

    expected_adjacent = [
        (position[0] + dirs2[d].x, position[1] + dirs2[d].y)
        for d in [
            Direction.UP,
            Direction.DOWN,
            Direction.LEFT,
            Direction.RIGHT,
        ]
    ]

    assert sorted(exits) == sorted(expected_adjacent)


def test_get_exits_blocked_position(client, pathfinder):
    position = (1, 1)
    collision_map = {position: MagicMock(endure=None, exit_from=[])}

    client.collision_manager.get_collision_map.return_value = collision_map
    client.boundary.is_within_boundaries.return_value = False

    assert pathfinder.get_exits(position, Direction.DOWN) == []


def test_get_exits_with_skip_nodes(client, pathfinder):
    client.collision_manager.is_tile_occupied.return_value = False
    position = (1, 1)
    collision_map = {
        position: RegionProperties([], ["down"], [], None, None),
        (1, 2): RegionProperties(["up"], [], [], None, None),
        (2, 1): RegionProperties(["left"], ["up"], [], None, None),
    }

    client.collision_manager.get_collision_map.return_value = collision_map
    client.boundary.is_within_boundaries.return_value = True

    exits = pathfinder.get_exits(position, Direction.DOWN, skip_nodes={(2, 1)})
    assert exits == [(1, 2)]


def test_get_exits_invalid_boundaries(client, pathfinder):
    position = (1, 1)
    collision_map = {
        position: MagicMock(endure=None, exit_from=["down"]),
        (1, 2): MagicMock(endure=None, exit_from=[]),
    }

    client.collision_manager.get_collision_map.return_value = collision_map
    client.boundary.is_within_boundaries.return_value = False

    assert pathfinder.get_exits(position, Direction.DOWN) == []


def test_pathfind_multi_step(client, pathfinder):
    client.collision_manager.get_collision_map.return_value = {}
    client.npc_manager.get_entity_pos.return_value = None

    pathfinder.get_exits = MagicMock(
        side_effect=[
            [(1, 0)],  # from (0, 0)
            [(2, 0)],  # from (1, 0)
            [],  # from (2, 0)
        ]
    )

    result = pathfinder.pathfind((0, 0), (2, 0), Direction.RIGHT)
    assert result == [(2, 0), (1, 0)]


def test_pathfind_avoids_cycles(client, pathfinder):
    client.collision_manager.get_collision_map.return_value = {}
    client.npc_manager.get_entity_pos.return_value = None

    pathfinder.get_exits = MagicMock(
        side_effect=[
            [(0, 1)],  # from (0, 0)
            [(0, 0), (1, 1)],  # from (0, 1)
            [],  # from (1, 1)
        ]
    )

    result = pathfinder.pathfind((0, 0), (1, 1), Direction.DOWN)
    assert result == [(1, 1), (0, 1)]


def test_pathfind_skips_blocked_tile(client, pathfinder):
    client.collision_manager.get_collision_map.return_value = {}
    client.npc_manager.get_entity_pos.return_value = None
    pathfinder.get_exits = MagicMock(return_value=[])

    assert pathfinder.pathfind((0, 0), (1, 1), Direction.DOWN) is None


def test_get_exits_respects_facing(client, pathfinder):
    client.collision_manager.is_tile_occupied.return_value = False
    position = (1, 1)
    collision_map = {
        position: RegionProperties([], ["up"], [], None, None),
        (1, 0): RegionProperties(["down"], [], [], None, None),
    }

    client.collision_manager.get_collision_map.return_value = collision_map
    client.boundary.is_within_boundaries.return_value = True

    assert pathfinder.get_exits(position, Direction.UP) == [(1, 0)]
