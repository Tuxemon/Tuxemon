# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock

import pytest

from tuxemon.db import Direction, FacingMode
from tuxemon.entity.path.controller import PathController
from tuxemon.entity.path.path_view import PathView
from tuxemon.map.map import dirs2, tile_distance, vector2_to_tile_pos
from tuxemon.math import Vector2


class SimpleNPC:
    """Small real object for attributes mutated by PathController."""

    def __init__(
        self, tile_pos=(0, 0), position=(0.0, 0.0), facing=Direction.DOWN
    ):
        self.slug = "test-npc"
        self.position = Vector2(position)
        self.tile_pos = tile_pos
        self.facing = facing
        self.moving = False
        self.move_direction = None
        self.ignore_collisions = False
        self.sprite_controller = None
        self.client = None
        self._moverate_modifier = 1.0
        self.mover = MoverCompat(self)

    def set_facing(self, d):
        self.facing = d
        if self.mover:
            self.mover.facing = d

    def set_move_direction(self, d=None):
        self.move_direction = d
        if self.mover:
            self.mover.move_direction = d

    def set_position(self, pos):
        self.position = Vector2(float(pos[0]), float(pos[1]))
        self.tile_pos = vector2_to_tile_pos(self.position)

    def on_tile_changed(self):
        pass

    def remove_collision(self):
        pass

    def stop_moving(self):
        self.moving = False

    def set_moverate_modifier(self, m):
        self._moverate_modifier = m
        if self.mover:
            self.mover.set_moverate_modifier(m)

    def begin_tile_exit(self):
        self.remove_collision()

    def complete_tile_entry(self, tile_pos):
        self.set_position(tile_pos)
        self.on_tile_changed()


class MoverCompat:
    """Compatibility wrapper for test doubles to mimic Mover interface."""

    def __init__(self, owner):
        self._owner = owner
        self.moverate_modifier = 1.0
        self.move_direction = None
        self.facing = Direction.DOWN
        self.facing_mode = FacingMode.FOLLOW_MOVEMENT
        self.base_moverate = 0.0
        self.move = None

    def set_moverate_modifier(self, modifier):
        self.moverate_modifier = max(0.0, modifier)
        self._owner._moverate_modifier = self.moverate_modifier

    def set_move_direction(self, direction=None):
        self.move_direction = direction
        self._owner.move_direction = direction

    def set_facing(self, direction):
        self.facing = direction
        self._owner.facing = direction

    def set_facing_mode(self, facing_mode):
        self.facing_mode = facing_mode

    def set_moverate(self, moverate):
        self.base_moverate = moverate

    def has_reached_next_tile(self, origin, target):
        return True


@pytest.fixture
def mk_npc_with_mocks():
    def _mk():
        npc = SimpleNPC()
        npc.mover.move = MagicMock()
        npc.facing_mode = FacingMode.FOLLOW_MOVEMENT
        sprite = MagicMock()
        sprite.play_animation = MagicMock()
        sprite.stop_animation = MagicMock()
        npc.sprite_controller = sprite
        return npc

    return _mk


@pytest.fixture
def map_manager():
    return MagicMock()


@pytest.fixture
def pathfinder():
    return MagicMock()


@pytest.fixture
def npc_manager():
    return MagicMock()


@pytest.mark.parametrize(
    "a, b, expected",
    [
        pytest.param((0, 0), (3, 4), 5.0, id="3_4_5_triangle"),
        pytest.param((1.2, 2.3), (1.2, 2.3), 0.0, id="same_point"),
    ],
)
def test_tile_distance(a, b, expected):
    assert pytest.approx(tile_distance(a, b)) == expected


@pytest.mark.parametrize(
    "direction",
    [
        pytest.param(Direction.LEFT, id="left"),
        pytest.param(Direction.RIGHT, id="right"),
        pytest.param(Direction.UP, id="up"),
        pytest.param(Direction.DOWN, id="down"),
    ],
)
def test_move_one_tile_appends_expected_tile(
    mk_npc_with_mocks, pathfinder, map_manager, npc_manager, direction
):
    npc = mk_npc_with_mocks()
    npc.tile_pos = (4, 4)
    pc = PathController(npc, pathfinder, map_manager, npc_manager)

    pc.move_one_tile(direction)

    expected = vector2_to_tile_pos(Vector2(npc.tile_pos) + dirs2[direction])
    assert pc.path.next() == expected


def test_start_path_sets_path_and_calls_next_waypoint(
    mk_npc_with_mocks, map_manager, npc_manager
):
    pf = MagicMock()
    pf.pathfind.return_value = [(0, 1), (0, 2)]
    pf.is_tile_traversable.return_value = True
    npc = mk_npc_with_mocks()
    npc.tile_pos = (0, 0)
    pc = PathController(npc, pf, map_manager, npc_manager)
    pc.start_path((0, 2))
    assert list(pc.path) == [(0, 1), (0, 2)]
    npc.sprite_controller.play_animation.assert_called_once()
    npc.mover.move.assert_called()


def test_start_path_no_path_returns_no_changes(
    mk_npc_with_mocks, map_manager, npc_manager
):
    pf = MagicMock()
    pf.pathfind.return_value = []
    npc = mk_npc_with_mocks()
    npc.tile_pos = (1, 1)
    pc = PathController(npc, pf, map_manager, npc_manager)
    pc.pathfinding = (5, 5)
    pc.start_path((5, 5))
    assert len(pc.path) == 0
    assert pc.exec.origin is None
    assert pc.exec.target is None
    assert pc.pathfinding is None


def test_next_waypoint_blocked_calls_handle_obstruction(
    mk_npc_with_mocks, map_manager, npc_manager
):
    pf = MagicMock()
    pf.is_tile_traversable.return_value = False
    npc = mk_npc_with_mocks()
    pc = PathController(npc, pf, map_manager, npc_manager)
    pc.path = PathView([(0, 1)])
    pc.reroute_policy.on_obstruction = MagicMock()
    pc.next_waypoint()
    pc.reroute_policy.on_obstruction(npc, npc_manager, pc.pathfinding, (0, 1))
    assert not npc.moving


def test_next_waypoint_traversable(
    mk_npc_with_mocks, map_manager, npc_manager
):
    pf = MagicMock()
    pf.is_tile_traversable.return_value = True
    npc = mk_npc_with_mocks()
    npc.tile_pos = (3, 3)
    pc = PathController(npc, pf, map_manager, npc_manager)
    pc.path = PathView([(3, 4)])
    pc.next_waypoint()
    npc.sprite_controller.play_animation.assert_called_once()
    assert pc.exec.origin == (3, 3)
    assert pc.exec.target == (3, 4)
    npc.mover.move.assert_called_once_with(Direction.DOWN)


def test_next_waypoint_exception_cancels_path(
    mk_npc_with_mocks, map_manager, npc_manager
):
    pf = MagicMock()
    pf.is_tile_traversable.side_effect = RuntimeError("boom")
    npc = mk_npc_with_mocks()
    pc = PathController(npc, pf, map_manager, npc_manager)
    pc.path = PathView([(0, 1)])
    pc.next_waypoint()
    assert len(pc.path) == 0
    assert pc.exec.origin is None
    assert pc.exec.target is None


def test_cancel_movement_preserve_and_abort(
    mk_npc_with_mocks, pathfinder, map_manager, npc_manager
):
    npc = mk_npc_with_mocks()
    pc = PathController(npc, pathfinder, map_manager, npc_manager)
    pc.path_origin = (2, 2)
    pc.path = PathView([])
    npc.position = Vector2(2.0, 2.0)
    pc.cancel_movement()
    assert len(pc.path) == 0


def test_abort_movement_reverts_tile_pos(
    mk_npc_with_mocks, pathfinder, map_manager, npc_manager
):
    npc = mk_npc_with_mocks()
    pc = PathController(npc, pathfinder, map_manager, npc_manager)
    npc.tile_pos = (7, 7)
    pc.exec.origin = (3, 3)
    pc.exec.target = (3, 4)
    pc.abort_movement(preserve_position=False)
    assert npc.tile_pos == (3, 3)
    assert not npc.moving
    assert len(pc.path) == 0


def test_stress_obstruction_loop(mk_npc_with_mocks, map_manager, npc_manager):
    pf = MagicMock()
    pf.pathfind.return_value = [(0, 1)]
    pf.is_tile_traversable.return_value = False
    npc_manager.get_entity_pos.return_value = None
    npc = mk_npc_with_mocks()
    pc = PathController(npc, pf, map_manager, npc_manager)
    pc.pathfinding = (0, 1)
    pc.path = PathView([(0, 1)])
    for _ in range(100):
        pc.next_waypoint()
    assert True


@pytest.mark.parametrize(
    "steps, expected_calls",
    [
        pytest.param(60, 1, id="one_second"),
        pytest.param(120, 1, id="two_seconds"),
    ],
)
def test_stress_cooldown_throttling(
    mk_npc_with_mocks, map_manager, npc_manager, steps, expected_calls
):
    pf = MagicMock()
    pf.pathfind.return_value = [(1, 1)]
    pf.is_tile_traversable.return_value = True

    npc = mk_npc_with_mocks()
    pc = PathController(npc, pf, map_manager, npc_manager)

    map_manager.collision_map.get.return_value = None
    pc.pathfinding = (1, 1)
    pc._repath_cooldown = 1.0

    for _ in range(steps):
        pc.update(1.0 / 60.0)
        pc.process_movement()

    assert pf.pathfind.call_count == expected_calls


def test_cancel_movement_preserve_and_abort_behavior(
    mk_npc_with_mocks, pathfinder, map_manager, npc_manager
):
    npc = mk_npc_with_mocks()
    pc = PathController(npc, pathfinder, map_manager, npc_manager)
    pc.path_origin = (2, 2)
    pc.path = PathView([])
    npc.position = Vector2(2.0, 2.0)
    pc.cancel_movement()
    assert len(pc.path) == 0


def test_handle_obstruction_recalculates_when_npc_blocking(
    pathfinder, map_manager
):
    blocking_npc = MagicMock()
    npc_manager = MagicMock()
    npc_manager.get_entity_pos.return_value = blocking_npc
    npc = MagicMock()
    pc = PathController(npc, pathfinder, map_manager, npc_manager)
    pc.pathfinding = (9, 9)
    pc.start_path = MagicMock()
    commands = pc.reroute_policy.on_obstruction(
        npc, npc_manager, pc.pathfinding, (0, 0)
    )
    for cmd in commands:
        pc.execute_command(cmd)

    pc.start_path.assert_called_once_with((9, 9))


def test_handle_obstruction_no_pathfinding_logs(
    mk_npc_with_mocks, pathfinder, map_manager, npc_manager
):
    npc = mk_npc_with_mocks()
    pc = PathController(npc, pathfinder, map_manager, npc_manager)
    pc.reroute_policy.on_obstruction(npc, npc_manager, pc.pathfinding, (0, 1))


def test_handle_obstruction_with_npc_sets_cooldown_and_retries_path(
    mk_npc_with_mocks, map_manager
):
    pf = MagicMock()
    pf.pathfind.return_value = [(0, 1), (0, 2)]
    pf.is_tile_traversable.return_value = True
    npc_manager = MagicMock()
    blocking_npc = MagicMock()
    blocking_npc.slug = "blocker"
    npc_manager.get_entity_pos.return_value = blocking_npc
    npc = mk_npc_with_mocks()
    pc = PathController(npc, pf, map_manager, npc_manager)
    pc.pathfinding = (0, 2)
    commands = pc.reroute_policy.on_obstruction(
        npc, npc_manager, pc.pathfinding, (0, 1)
    )
    for cmd in commands:
        pc.execute_command(cmd)

    assert pc._repath_cooldown == 0.5
    pf.pathfind.assert_called_once_with(npc.tile_pos, (0, 2), npc.facing)


def test_handle_obstruction_without_npc_sets_cooldown_and_stops(
    mk_npc_with_mocks, pathfinder, map_manager
):
    npc_manager = MagicMock()
    npc_manager.get_entity_pos.return_value = None
    npc = mk_npc_with_mocks()
    pc = PathController(npc, pathfinder, map_manager, npc_manager)
    pc.pathfinding = (5, 5)
    pc.path = PathView([(5, 5)])
    commands = pc.reroute_policy.on_obstruction(
        npc, npc_manager, pc.pathfinding, (4, 4)
    )
    for cmd in commands:
        pc.execute_command(cmd)

    assert pc._repath_cooldown == 1.0
    assert list(pc.path) == [(5, 5)]
    assert not npc.moving


def test_process_movement_direct_move_when_no_path(
    mk_npc_with_mocks, map_manager
):
    pf = MagicMock()
    pf.is_tile_traversable.return_value = True
    npc = mk_npc_with_mocks()
    npc.tile_pos = (0, 0)
    npc.move_direction = npc.facing.DOWN
    pc = PathController(npc, pf, map_manager, MagicMock())
    pc.path = PathView([])
    pc.process_movement()
    assert pc.path


def test_update_triggers_process(
    mk_npc_with_mocks, pathfinder, map_manager, npc_manager
):
    npc = mk_npc_with_mocks()
    pc = PathController(npc, pathfinder, map_manager, npc_manager)
    pc.update(0.016)
    pc.path = PathView([(1, 1)])
    pc.update(0.016)


def test_process_movement_does_not_retry_path_when_cooldown_active(
    mk_npc_with_mocks, pathfinder, map_manager, npc_manager
):
    pf = MagicMock()
    npc = mk_npc_with_mocks()
    pc = PathController(npc, pf, map_manager, npc_manager)
    pc.pathfinding = (3, 3)
    pc._repath_cooldown = 0.5
    pc.process_movement()
    pf.pathfind.assert_not_called()


def test_process_movement_retries_path_when_cooldown_expires(
    mk_npc_with_mocks, map_manager
):
    pf = MagicMock()
    pf.pathfind.return_value = [(0, 1), (0, 2)]
    pf.is_tile_traversable.return_value = True
    npc = mk_npc_with_mocks()
    pc = PathController(npc, pf, map_manager, MagicMock())
    pc.pathfinding = (0, 2)
    pc._repath_cooldown = 0.0
    pc.process_movement()
    pf.pathfind.assert_called_once_with(npc.tile_pos, (0, 2), npc.facing)


@pytest.mark.parametrize(
    "initial_cooldown, delta, expected",
    [
        pytest.param(1.0, 0.3, 0.7, id="partial_reduce"),
        pytest.param(1.0, 1.0, 0.0, id="full_reduce"),
    ],
)
def test_update_reduces_repath_cooldown(
    mk_npc_with_mocks,
    pathfinder,
    map_manager,
    npc_manager,
    initial_cooldown,
    delta,
    expected,
):
    npc = mk_npc_with_mocks()
    pc = PathController(npc, pathfinder, map_manager, npc_manager)
    pc._repath_cooldown = initial_cooldown
    pc.update(delta)
    assert pytest.approx(pc._repath_cooldown) == expected


@pytest.mark.parametrize(
    "blocking, expected_cooldown",
    [
        pytest.param(None, None, id="no_blocker"),
        pytest.param("blocker", 0.5, id="blocked_sets_cooldown"),
    ],
)
def test_obstruction_handling(
    mk_npc_with_mocks, map_manager, blocking, expected_cooldown
):
    pf = MagicMock()
    pf.pathfind.return_value = [(1, 1)]
    pf.is_tile_traversable.return_value = False

    npc_manager = MagicMock()
    if blocking:
        npc = MagicMock()
        npc.slug = blocking
        npc_manager.get_entity_pos.return_value = npc
    else:
        npc_manager.get_entity_pos.return_value = None

    npc = mk_npc_with_mocks()
    pc = PathController(npc, pf, map_manager, npc_manager)
    pc.pathfinding = (1, 1)
    pc.path = PathView([(1, 1)])

    for _ in range(10):
        pc.next_waypoint()

    if expected_cooldown is not None:
        assert pc._repath_cooldown == expected_cooldown
    else:
        assert True


@pytest.mark.parametrize(
    "path_return, expected_len",
    [
        pytest.param([(1, 1), (2, 2)], 2, id="two_steps"),
        pytest.param([(x, x) for x in range(10)], 10, id="ten_steps"),
    ],
)
def test_retry_path_after_cooldown(
    mk_npc_with_mocks, map_manager, npc_manager, path_return, expected_len
):
    pf = MagicMock()
    pf.pathfind.side_effect = lambda *_: path_return
    pf.is_tile_traversable.return_value = True

    npc = mk_npc_with_mocks()
    npc.tile_pos = (0, 0)
    pc = PathController(npc, pf, map_manager, npc_manager)

    map_manager.collision_map.get.return_value = None
    pc.pathfinding = path_return[-1]
    pc._repath_cooldown = 0.0

    for _ in range(20):
        pc.process_movement()

    assert len(pc.path) <= expected_len
