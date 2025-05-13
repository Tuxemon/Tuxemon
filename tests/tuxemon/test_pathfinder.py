# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import MagicMock

from tuxemon.boundary import BoundaryChecker
from tuxemon.client import LocalPygameClient
from tuxemon.db import Direction
from tuxemon.map import RegionProperties, dirs2
from tuxemon.map_manager import MapManager
from tuxemon.movement import Pathfinder, PathfindNode, get_tile_moverate
from tuxemon.npc import NPC
from tuxemon.prepare import CONFIG
from tuxemon.states.world.worldstate import WorldState


class TestPathfinder(unittest.TestCase):
    def setUp(self):
        self.client = MagicMock(spec=LocalPygameClient)
        self.client.map_manager = MagicMock(spec=MapManager)
        self.client.map_manager.map_size = (10, 10)
        self.client.map_manager.collision_lines_map = {}
        self.client.boundary = MagicMock(spec=BoundaryChecker)
        self.world_state = MagicMock(spec=WorldState)
        self.world_state.player = MagicMock(spec=NPC)
        self.world_state.player.facing = MagicMock(spec=Direction)
        self.pathfinder = Pathfinder(self.client, self.world_state)

    def test_pathfind_success(self):
        start = (0, 0)
        dest = (1, 1)
        self.world_state.get_collision_map.return_value = {}
        self.world_state.get_entity_pos.return_value = None

        node1 = MagicMock(spec=PathfindNode)
        node1.get_value.return_value = start
        node1.get_parent.return_value = None
        node1.reconstruct_path.return_value = [start]

        node2 = MagicMock(spec=PathfindNode)
        node2.get_value.return_value = dest
        node2.get_parent.return_value = node1
        node2.reconstruct_path.return_value = [start, dest]

        self.pathfinder.pathfind_r = MagicMock(return_value=node2)

        path = self.pathfinder.pathfind(start, dest, Direction.down)

        self.assertEqual(path, [start, dest])

    def test_pathfind_failure(self):
        start = (0, 0)
        dest = (1, 1)
        self.world_state.get_collision_map.return_value = {}
        self.world_state.get_entity_pos.return_value = None

        self.pathfinder.pathfind_r = MagicMock(return_value=None)

        path = self.pathfinder.pathfind(start, dest, Direction.down)

        self.assertIsNone(path)
        self.world_state.get_entity_pos.assert_called_once_with(start)

    def test_is_valid_position(self):
        position = (1, 1)
        skip_nodes = {(2, 2)}

        self.client.boundary.is_within_boundaries.return_value = True

        self.assertTrue(
            self.pathfinder.is_valid_position(position, skip_nodes)
        )

        self.client.boundary.is_within_boundaries.return_value = False
        self.assertFalse(
            self.pathfinder.is_valid_position(position, skip_nodes)
        )

        self.client.boundary.is_within_boundaries.return_value = True
        self.assertFalse(self.pathfinder.is_valid_position((2, 2), skip_nodes))

    def test_is_tile_traversable(self):
        npc = MagicMock(spec=NPC)
        npc.tile_pos = (1, 1)
        npc.ignore_collisions = False
        npc.facing = Direction.down
        tile = (1, 2)

        self.pathfinder.get_exits = MagicMock(return_value=[tile])
        self.world_state.get_entity_pos = MagicMock(return_value=None)

        self.assertTrue(self.pathfinder.is_tile_traversable(npc, tile))

        other_npc = MagicMock()
        other_npc.moving = True
        other_npc.moverate = CONFIG.player_walkrate
        other_npc.facing = Direction.up
        self.world_state.get_entity_pos.return_value = other_npc
        self.assertFalse(self.pathfinder.is_tile_traversable(npc, tile))

        npc.ignore_collisions = True
        self.assertTrue(self.pathfinder.is_tile_traversable(npc, tile))

    def test_get_tile_moverate(self):
        npc = MagicMock(spec=NPC)
        destination = (1, 1)

        self.world_state.surface_map = {destination: {"speed_modifier": 0.5}}
        npc.moverate = 2.0

        moverate = get_tile_moverate(
            self.world_state.surface_map, npc, destination
        )

        expected_moverate = npc.moverate * 0.5  # 2.0 * 0.5
        self.assertEqual(moverate, expected_moverate)

    def test_get_tile_moverate_no_properties(self):
        npc = MagicMock(spec=NPC)
        destination = (1, 1)

        self.world_state.surface_map = {destination: {}}
        npc.moverate = 2.0

        moverate = get_tile_moverate(
            self.world_state.surface_map, npc, destination
        )

        expected_moverate = npc.moverate * 1.0  # 2.0 * 1.0
        self.assertEqual(moverate, expected_moverate)

    def test_pathfind_r_with_no_nodes(self):
        dest = (1, 1)
        queue = []
        known_nodes = set()

        result = self.pathfinder.pathfind_r(
            dest, queue, known_nodes, Direction.down
        )

        self.assertIsNone(result)

    def test_pathfind_r_reaches_destination(self):
        start = (0, 0)
        dest = (1, 1)
        node1 = MagicMock(spec=PathfindNode)
        node1.get_value.return_value = start
        node1.get_parent.return_value = None

        node2 = MagicMock(spec=PathfindNode)
        node2.get_value.return_value = dest
        node2.get_parent.return_value = node1

        self.pathfinder.get_exits = MagicMock(return_value=[dest])
        self.pathfinder.pathfind_r = MagicMock(return_value=node2)

        result = self.pathfinder.pathfind_r(
            dest, [node1], set(), Direction.down
        )

        self.assertEqual(result, node2)

    def test_pathfind_with_same_start_and_dest(self):
        start = (1, 1)
        dest = (1, 1)
        self.world_state.get_collision_map.return_value = {}
        self.world_state.get_entity_pos.return_value = None
        path = self.pathfinder.pathfind(start, dest, Direction.down)
        self.assertEqual(path, [])

    def test_is_valid_position_out_of_bounds(self):
        position = (10, 10)
        skip_nodes = set()
        self.client.boundary.is_within_boundaries.return_value = False
        self.assertFalse(
            self.pathfinder.is_valid_position(position, skip_nodes)
        )

    def test_is_tile_traversable_with_no_npcs(self):
        npc = MagicMock(spec=NPC)
        npc.tile_pos = (1, 1)
        npc.ignore_collisions = False
        npc.facing = Direction.down
        tile = (1, 2)
        self.pathfinder.get_exits = MagicMock(return_value=[tile])
        self.world_state.get_entity_pos = MagicMock(return_value=None)
        self.assertTrue(self.pathfinder.is_tile_traversable(npc, tile))

    def test_get_tile_moverate_with_no_surface_data(self):
        npc = MagicMock(spec=NPC)
        destination = (1, 1)
        self.world_state.surface_map = {}
        npc.moverate = 2.0
        moverate = get_tile_moverate(
            self.world_state.surface_map, npc, destination
        )
        expected_moverate = npc.moverate * 1.0
        self.assertEqual(moverate, expected_moverate)

    def test_pathfind_r_with_multiple_exits(self):
        start = (0, 0)
        dest = (1, 1)
        node1 = MagicMock(spec=PathfindNode)
        node1.get_value.return_value = start
        node2 = MagicMock(spec=PathfindNode)
        node2.get_value.return_value = dest
        self.pathfinder.get_exits = MagicMock(return_value=[(1, 1), (0, 1)])
        self.pathfinder.pathfind_r = MagicMock(return_value=node2)
        result = self.pathfinder.pathfind_r(
            dest, [node1], set(), Direction.down
        )
        self.assertEqual(result, node2)

    def test_pathfind_r_no_adjacent_nodes(self):
        start = (0, 0)
        dest = (1, 1)
        node1 = MagicMock(spec=PathfindNode)
        node1.get_value.return_value = start
        self.pathfinder.get_exits = MagicMock(return_value=[])
        result = self.pathfinder.pathfind_r(
            dest, [node1], set(), Direction.down
        )
        self.assertIsNone(result)

    def test_get_exits_with_tile_data(self):
        position = (1, 1)
        collision_map = {
            position: RegionProperties(
                enter_from=[],
                exit_from=["down", "right"],
                endure=[],
                entity=None,
                key=None,
            ),
            (1, 2): RegionProperties(
                enter_from=["up"],
                exit_from=[],
                endure=[],
                entity=None,
                key=None,
            ),
            (2, 1): RegionProperties(
                enter_from=["left"],
                exit_from=["up"],
                endure=[],
                entity=None,
                key=None,
            ),
        }
        self.world_state.get_collision_map.return_value = collision_map
        self.client.boundary.is_within_boundaries.return_value = True

        exits = self.pathfinder.get_exits(position, Direction.down)

        expected_exits = [(1, 2), (2, 1)]
        self.assertEqual(exits, expected_exits)

    def test_get_exits_with_no_valid_exits(self):
        position = (1, 1)
        collision_map = {
            position: MagicMock(endure=None, exit_from=[]),
        }
        self.world_state.get_collision_map.return_value = collision_map
        self.client.boundary.is_within_boundaries.return_value = True

        exits = self.pathfinder.get_exits(position, Direction.down)

        expected_adjacent_tiles = [
            (
                position[0] + dirs2[Direction.up].x,
                position[1] + dirs2[Direction.up].y,
            ),
            (
                position[0] + dirs2[Direction.down].x,
                position[1] + dirs2[Direction.down].y,
            ),
            (
                position[0] + dirs2[Direction.left].x,
                position[1] + dirs2[Direction.left].y,
            ),
            (
                position[0] + dirs2[Direction.right].x,
                position[1] + dirs2[Direction.right].y,
            ),
        ]
        self.assertEqual(sorted(exits), sorted(expected_adjacent_tiles))

    def test_get_exits_with_blocked_position(self):
        position = (1, 1)
        collision_map = {
            position: MagicMock(endure=None, exit_from=[]),
        }
        self.world_state.get_collision_map.return_value = collision_map
        self.client.boundary.is_within_boundaries.return_value = False

        exits = self.pathfinder.get_exits(position, Direction.down)

        self.assertEqual(exits, [])

    def test_get_exits_with_skip_nodes(self):
        position = (1, 1)
        collision_map = {
            position: RegionProperties(
                enter_from=[],
                exit_from=["down"],
                endure=[],
                entity=None,
                key=None,
            ),
            (1, 2): RegionProperties(
                enter_from=["up"],
                exit_from=[],
                endure=[],
                entity=None,
                key=None,
            ),
            (2, 1): RegionProperties(
                enter_from=["left"],
                exit_from=["up"],
                endure=[],
                entity=None,
                key=None,
            ),
        }
        self.world_state.get_collision_map.return_value = collision_map
        self.client.boundary.is_within_boundaries.return_value = True

        skip_nodes = {(2, 1)}
        exits = self.pathfinder.get_exits(
            position=position, facing=Direction.down, skip_nodes=skip_nodes
        )
        expected_exits = [(1, 2)]
        self.assertEqual(exits, expected_exits)

    def test_get_exits_with_invalid_boundaries(self):
        position = (1, 1)
        collision_map = {
            position: MagicMock(endure=None, exit_from=["down"]),
            (1, 2): MagicMock(endure=None, exit_from=[]),
        }
        self.world_state.get_collision_map.return_value = collision_map
        self.client.boundary.is_within_boundaries.return_value = False

        exits = self.pathfinder.get_exits(position, Direction.down)

        self.assertEqual(exits, [])
