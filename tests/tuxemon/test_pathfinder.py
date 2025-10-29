# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import MagicMock

from tuxemon.boundary import BoundaryChecker
from tuxemon.client import LocalPygameClient
from tuxemon.db import Direction
from tuxemon.map.collision_manager import CollisionManager
from tuxemon.map.map import dirs2
from tuxemon.map.map_manager import MapManager
from tuxemon.map.map_region import RegionProperties
from tuxemon.movement import Pathfinder
from tuxemon.npc import NPC
from tuxemon.npc_manager import NPCManager
from tuxemon.prepare import CONFIG


class TestPathfinder(unittest.TestCase):
    def setUp(self):
        self.client = MagicMock(spec=LocalPygameClient)
        self.client.map_manager = MagicMock(spec=MapManager)
        self.client.map_manager.map_size = (10, 10)
        self.client.map_manager.collision_lines_map = {}
        self.client.boundary = MagicMock(spec=BoundaryChecker)
        self.client.npc_manager = MagicMock(spec=NPCManager)
        self.client.collision_manager = MagicMock(spec=CollisionManager)
        self.pathfinder = Pathfinder(
            self.client.npc_manager,
            self.client.map_manager,
            self.client.collision_manager,
            self.client.boundary,
        )

    def test_pathfind_success(self):
        start = (0, 0)
        dest = (1, 1)
        self.client.collision_manager.get_collision_map.return_value = {}
        self.client.npc_manager.get_entity_pos.return_value = None

        # No exits from start
        self.pathfinder.get_exits = MagicMock(return_value=[])

        path = self.pathfinder.pathfind(start, dest, Direction.down)

        self.assertIsNone(path)

    def test_pathfind_failure(self):
        start = (0, 0)
        dest = (1, 1)
        self.client.collision_manager.get_collision_map.return_value = {}
        self.client.npc_manager.get_entity_pos.return_value = None

        self.pathfinder.get_exits = MagicMock(return_value=[])

        path = self.pathfinder.pathfind(start, dest, Direction.down)

        self.assertIsNone(path)

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
        tile = (1, 2)

        self.pathfinder.get_exits = MagicMock(return_value=[tile])
        self.client.npc_manager.get_entity_pos = MagicMock(return_value=None)

        result = self.pathfinder.is_tile_traversable(
            (1, 1), Direction.down, tile, False
        )
        self.assertTrue(result)

        other_npc = MagicMock()
        other_npc.moving = True
        other_npc.moverate = CONFIG.player_walkrate
        other_npc.facing = Direction.up
        self.client.npc_manager.get_entity_pos.return_value = other_npc
        result = self.pathfinder.is_tile_traversable(
            (1, 1), Direction.down, tile, False
        )
        self.assertFalse(result)

        result = self.pathfinder.is_tile_traversable(
            (1, 1), Direction.down, tile, True
        )
        self.assertTrue(result)

    def test_pathfind_with_same_start_and_dest(self):
        start = (1, 1)
        dest = (1, 1)
        self.client.collision_manager.get_collision_map.return_value = {}
        self.client.npc_manager.get_entity_pos.return_value = None
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
        tile = (1, 2)
        self.pathfinder.get_exits = MagicMock(return_value=[tile])
        self.client.npc_manager.get_entity_pos = MagicMock(return_value=None)
        result = self.pathfinder.is_tile_traversable(
            (1, 1), Direction.down, tile, False
        )
        self.assertTrue(result)

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
        self.client.collision_manager.get_collision_map.return_value = (
            collision_map
        )
        self.client.boundary.is_within_boundaries.return_value = True

        exits = self.pathfinder.get_exits(position, Direction.down)

        expected_exits = [(1, 2), (2, 1)]
        self.assertEqual(exits, expected_exits)

    def test_get_exits_with_no_valid_exits(self):
        position = (1, 1)
        collision_map = {
            position: MagicMock(endure=None, exit_from=[]),
        }
        self.client.collision_manager.get_collision_map.return_value = (
            collision_map
        )
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
        self.client.collision_manager.get_collision_map.return_value = (
            collision_map
        )
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
        self.client.collision_manager.get_collision_map.return_value = (
            collision_map
        )
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
        self.client.collision_manager.get_collision_map.return_value = (
            collision_map
        )
        self.client.boundary.is_within_boundaries.return_value = False

        exits = self.pathfinder.get_exits(position, Direction.down)

        self.assertEqual(exits, [])

    def test_pathfind_multi_step_success(self):
        start = (0, 0)
        dest = (2, 0)
        self.client.collision_manager.get_collision_map.return_value = {}
        self.client.npc_manager.get_entity_pos.return_value = None

        self.pathfinder.get_exits = MagicMock(
            side_effect=[
                [(1, 0)],  # from (0, 0)
                [(2, 0)],  # from (1, 0)
                [],  # from (2, 0)
            ]
        )

        path = self.pathfinder.pathfind(start, dest, Direction.right)
        self.assertEqual(path, [(2, 0), (1, 0)])

    def test_pathfind_avoids_cycles(self):
        start = (0, 0)
        dest = (1, 1)
        self.client.collision_manager.get_collision_map.return_value = {}
        self.client.npc_manager.get_entity_pos.return_value = None

        self.pathfinder.get_exits = MagicMock(
            side_effect=[
                [(0, 1)],  # from (0, 0)
                [(0, 0), (1, 1)],  # from (0, 1)
                [],  # from (1, 1)
            ]
        )

        path = self.pathfinder.pathfind(start, dest, Direction.down)

        self.assertEqual(path, [(1, 1), (0, 1)])

    def test_pathfind_skips_blocked_tile(self):
        start = (0, 0)
        dest = (1, 1)
        self.client.collision_manager.get_collision_map.return_value = {}

        # Simulate that no exits are available from (0, 0)
        self.pathfinder.get_exits = MagicMock(return_value=[])
        self.client.npc_manager.get_entity_pos.return_value = None

        path = self.pathfinder.pathfind(start, dest, Direction.down)

        self.assertIsNone(path)

    def test_get_exits_respects_facing(self):
        position = (1, 1)
        collision_map = {
            position: RegionProperties(
                enter_from=[],
                exit_from=["up"],  # Only allow exit upward
                endure=[],
                entity=None,
                key=None,
            ),
            (1, 0): RegionProperties(
                enter_from=["down"],
                exit_from=[],
                endure=[],
                entity=None,
                key=None,
            ),
        }
        self.client.collision_manager.get_collision_map.return_value = (
            collision_map
        )
        self.client.boundary.is_within_boundaries.return_value = True

        exits = self.pathfinder.get_exits(position, Direction.up)
        self.assertEqual(exits, [(1, 0)])

    def test_is_tile_traversable_blocked_by_npc(self):
        npc = MagicMock(spec=NPC)

        tile = (1, 2)
        self.pathfinder.get_exits = MagicMock(return_value=[tile])

        # Simulate a blocking NPC on a neighboring tile
        blocking_npc = MagicMock()
        blocking_npc.moving = True
        blocking_npc.moverate = CONFIG.player_walkrate
        blocking_npc.facing = Direction.up  # Opposite direction

        self.client.npc_manager.get_entity_pos = MagicMock(
            return_value=blocking_npc
        )
        self.client.map_manager.map_size = (10, 10)

        result = self.pathfinder.is_tile_traversable(
            (1, 1), Direction.down, tile, False
        )
        self.assertFalse(result)
