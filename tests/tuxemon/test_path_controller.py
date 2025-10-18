# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import MagicMock, Mock

from tuxemon.db import Direction
from tuxemon.entity_dir.path import PathController, tile_distance
from tuxemon.map.map import dirs2
from tuxemon.math import Vector2
from tuxemon.tools import vector2_to_tile_pos


class SimpleNPC:
    """Small real object for attributes mutated by PathController."""

    def __init__(
        self, tile_pos=(0, 0), position=(0.0, 0.0), facing=Direction.down
    ):
        self.slug = "test-npc"
        self.position = Vector2(position)
        self.tile_pos = tile_pos
        self.facing = facing
        self.moving = False
        self.move_direction = None
        self.ignore_collisions = False
        self.mover = None
        self.sprite_controller = None
        self.client = None
        self._moverate_modifier = 1.0

    def set_facing(self, d):
        self.facing = d

    def set_move_direction(self, d=None):
        self.move_direction = d

    def set_position(self, pos):
        self.tile_pos = pos
        self.position = Vector2(float(pos[0]), float(pos[1]))

    def remove_collision(self):
        pass

    def stop_moving(self):
        self.moving = False

    def set_moverate_modifier(self, m):
        self._moverate_modifier = m


class PathControllerMagicMockTests(unittest.TestCase):
    def mk_npc_with_mocks(
        self, *, pathfinder=None, npc_manager=None, map_manager=None
    ):
        npc = SimpleNPC()
        mover = MagicMock()
        mover.current_direction = Direction.down
        mover.move = MagicMock()
        npc.mover = mover
        sprite = MagicMock()
        sprite.play_animation = MagicMock()
        sprite.stop_animation = MagicMock()
        npc.sprite_controller = sprite
        client = MagicMock()
        client.pathfinder = pathfinder or MagicMock()
        client.npc_manager = npc_manager or MagicMock()
        client.map_manager = map_manager or MagicMock()
        npc.client = client
        return npc

    def test_tile_distance(self):
        test_cases = [
            ((0, 0), (3, 4), 5.0),
            ((1.2, 2.3), (1.2, 2.3), 0.0),
        ]
        for a, b, expected in test_cases:
            with self.subTest(a=a, b=b):
                self.assertAlmostEqual(tile_distance(a, b), expected)

    def test_start_path_sets_path_and_calls_next_waypoint_when_path_found(
        self,
    ):
        pf = MagicMock()
        pf.pathfind.return_value = [(0, 1), (0, 2)]
        pf.is_tile_traversable.return_value = True
        npc = self.mk_npc_with_mocks(pathfinder=pf)
        npc.tile_pos = (0, 0)
        pc = PathController(npc)
        pc.start_path((0, 2))
        self.assertEqual(pc.path, [(0, 1), (0, 2)])
        npc.sprite_controller.play_animation.assert_called_once()
        npc.mover.move.assert_called()

    def test_start_path_no_path_returns_no_changes(self):
        pf = MagicMock()
        pf.pathfind.return_value = []
        npc = self.mk_npc_with_mocks(pathfinder=pf)
        npc.tile_pos = (1, 1)
        pc = PathController(npc)
        pc.pathfinding = (5, 5)
        pc.start_path((5, 5))
        self.assertEqual(pc.path, [])
        self.assertIsNone(pc.path_origin)
        self.assertIsNone(pc.pathfinding)

    def test_process_movement_starts_pathfinding_when_flag_set(self):
        pf = MagicMock()
        pf.pathfind.return_value = [(2, 2)]
        npc = self.mk_npc_with_mocks(pathfinder=pf)
        npc.tile_pos = (0, 0)
        pc = PathController(npc)
        pc.pathfinding = (2, 2)
        pc.process_movement()
        pf.pathfind.assert_called_once_with(npc.tile_pos, (2, 2), npc.facing)
        self.assertEqual(pc.path, [(2, 2)])

    def test_next_waypoint_when_tile_blocked_calls_handle_obstruction(self):
        pf = MagicMock()
        pf.is_tile_traversable.return_value = False
        npc = self.mk_npc_with_mocks(pathfinder=pf)
        npc.tile_pos = (0, 0)
        pc = PathController(npc)
        pc.path = [(0, 1)]
        pc.handle_obstruction = MagicMock()
        pc.next_waypoint()
        pc.handle_obstruction.assert_called_once_with((0, 1))
        self.assertFalse(npc.moving)

    def test_next_waypoint_when_traversable_plays_and_moves_and_sets_origin(
        self,
    ):
        pf = MagicMock()
        pf.is_tile_traversable.return_value = True
        npc = self.mk_npc_with_mocks(pathfinder=pf)
        npc.tile_pos = (3, 3)
        pc = PathController(npc)
        pc.path = [(3, 4)]
        pc.next_waypoint()
        npc.sprite_controller.play_animation.assert_called_once()
        self.assertEqual(pc.path_origin, (3, 3))
        npc.mover.move.assert_called_once_with(npc.mover.current_direction)

    def test_next_waypoint_pathfinder_exception_cancels_path(self):
        pf = MagicMock()
        pf.is_tile_traversable.side_effect = RuntimeError("boom")
        npc = self.mk_npc_with_mocks(pathfinder=pf)
        npc.tile_pos = (0, 0)
        pc = PathController(npc)
        pc.path = [(0, 1)]
        pc.next_waypoint()
        self.assertEqual(pc.path, [])
        self.assertIsNone(pc.path_origin)

    def test_check_waypoint_pops_and_applies_tile_effects_and_continuation(
        self,
    ):
        pf = MagicMock()
        npc = self.mk_npc_with_mocks(pathfinder=pf)
        npc.tile_pos = (0, 0)
        pc = PathController(npc)
        pc.path = [(0, 1)]
        pc.path_origin = (0, 0)
        npc.position = Vector2(0.0, 1.0)
        pc._apply_tile_effects = MagicMock()
        pc.check_continue = MagicMock()
        pc.check_waypoint()
        self.assertEqual(npc.tile_pos, (0, 1))
        self.assertEqual(pc.path, [])
        pc._apply_tile_effects.assert_called_once()
        pc.check_continue.assert_called_once()

    def test_check_continue_with_endure_enqueue_move(self):
        tile = Mock()
        tile.endure = [Direction.up]
        map_manager = Mock()
        map_manager.collision_map = {(1, 1): tile}
        pf = MagicMock()
        npc_manager = MagicMock()
        npc = self.mk_npc_with_mocks(
            pathfinder=pf, map_manager=map_manager, npc_manager=npc_manager
        )
        npc.tile_pos = (1, 1)
        pc = PathController(npc)
        pc.check_continue()
        self.assertTrue(pc.path)

    def test_apply_tile_effects_push_and_speed_modifier(self):
        push = Mock()
        push.direction = Direction.left
        push.strength = 2
        tile = Mock()
        tile.push_effect = push
        tile.speed_modifier = 0.5
        map_manager = Mock()
        map_manager.collision_map = {(2, 2): tile}
        pf = MagicMock()
        pf.get_exits.return_value = [(1, 2)]
        npc = self.mk_npc_with_mocks(pathfinder=pf, map_manager=map_manager)
        npc.tile_pos = (2, 2)
        pc = PathController(npc)
        pc._apply_tile_effects()
        self.assertEqual(npc._moverate_modifier, 0.5)
        self.assertTrue(pc.path)

    def test_move_one_tile_appends_expected_tile(self):
        directions = [
            Direction.left,
            Direction.right,
            Direction.up,
            Direction.down,
        ]
        for direction in directions:
            with self.subTest(direction=direction):
                npc = self.mk_npc_with_mocks()
                npc.tile_pos = (4, 4)
                pc = PathController(npc)
                pc.move_one_tile(direction)
                expected = vector2_to_tile_pos(
                    Vector2(npc.tile_pos) + dirs2[direction]
                )
                self.assertEqual(pc.path[-1], expected)

    def test_move_multiple_tiles_honors_get_exits_and_appends_reversed(self):
        origin = (5, 5)
        pf = MagicMock()
        pf.get_exits.return_value = [(6, 5)]
        npc = self.mk_npc_with_mocks(pathfinder=pf)
        npc.tile_pos = origin
        pc = PathController(npc)
        pc.move_multiple_tiles(Direction.right, strength=3)
        self.assertTrue(pc.path)
        self.assertEqual(pc.path_origin, origin)

    def test_cancel_path_clears_pathfinding_state(self):
        npc = self.mk_npc_with_mocks()
        pc = PathController(npc)
        pc.path = [(1, 1)]
        pc.pathfinding = (9, 9)
        pc.path_origin = (0, 0)
        pc.cancel_path()
        self.assertEqual(pc.path, [])
        self.assertIsNone(pc.pathfinding)
        self.assertIsNone(pc.path_origin)

    def test_cancel_movement_preserve_and_abort_behavior(self):
        npc = self.mk_npc_with_mocks()
        pc = PathController(npc)
        pc.path_origin = (2, 2)
        pc.path = []
        npc.position = Vector2(2.0, 2.0)
        pc.cancel_movement()
        self.assertEqual(pc.path, [])

    def test_abort_movement_reverts_tile_pos_when_not_preserve(self):
        npc = self.mk_npc_with_mocks()
        pc = PathController(npc)
        npc.tile_pos = (7, 7)
        pc.path_origin = (3, 3)
        pc.abort_movement(preserve_position=False)
        self.assertEqual(npc.tile_pos, (3, 3))
        self.assertFalse(npc.moving)
        self.assertEqual(pc.path, [])

    def test_handle_obstruction_recalculates_when_npc_blocking(self):
        pf = MagicMock()
        blocking_npc = SimpleNPC()
        npc_manager = MagicMock()
        npc_manager.get_entity_pos.return_value = blocking_npc

        client = MagicMock()
        client.pathfinder = pf
        client.npc_manager = npc_manager

        npc = SimpleNPC()
        npc.client = client
        pc = PathController(npc)
        pc.pathfinding = (9, 9)

        pc.start_path = MagicMock()
        pc.handle_obstruction((0, 0))
        pc.start_path.assert_called_once_with((9, 9))

    def test_handle_obstruction_no_pathfinding_logs_and_no_error(self):
        pf = MagicMock()
        npc = self.mk_npc_with_mocks(pathfinder=pf)
        pc = PathController(npc)
        pc.handle_obstruction((0, 1))

    def test_process_movement_direct_move_when_no_path(self):
        pf = MagicMock()
        pf.is_tile_traversable.return_value = True
        npc = self.mk_npc_with_mocks(pathfinder=pf)
        npc.tile_pos = (0, 0)
        npc.move_direction = Direction.down
        pc = PathController(npc)
        pc.path = []
        pc.process_movement()
        self.assertTrue(pc.path)

    def test_update_triggers_process_when_path_or_move_dir_present(self):
        pf = MagicMock()
        npc = self.mk_npc_with_mocks(pathfinder=pf)
        pc = PathController(npc)
        pc.update(0.016)
        pc.path = [(1, 1)]
        pc.update(0.016)

    def test_cancel_movement_before_leaving_tile_aborts(self):
        npc = self.mk_npc_with_mocks()
        pc = PathController(npc)
        pc.path_origin = (2, 2)
        npc.tile_pos = (2, 2)
        npc.position = Vector2(2.0, 2.0)
        npc.moving = False
        pc.abort_movement = MagicMock()
        pc.cancel_movement()
        pc.abort_movement.assert_called_once_with(preserve_position=True)
        self.assertEqual(pc.path, [])

    def test_check_continue_multiple_endure_uses_facing(self):
        tile = Mock()
        tile.endure = [Direction.up, Direction.down]
        map_manager = Mock()
        map_manager.collision_map = {(1, 1): tile}
        pf = MagicMock()
        npc = self.mk_npc_with_mocks(pathfinder=pf, map_manager=map_manager)
        npc.tile_pos = (1, 1)
        npc.set_facing(Direction.right)
        pc = PathController(npc)
        pc.move_one_tile = MagicMock()
        pc.check_continue()
        pc.move_one_tile.assert_called_once_with(Direction.right)
