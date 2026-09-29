# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import pytest

from tuxemon.db import Direction
from tuxemon.entity.entity import Body, EntityState, Mover
from tuxemon.math import Vector2
from tuxemon.prepare import CONFIG


@pytest.fixture
def body():
    return Body(position=Vector2(0, 0))


@pytest.fixture
def mover(body):
    return Mover(body)


def test_initial_state(mover, body):
    assert mover.state == EntityState.IDLE
    assert mover.facing == Direction.DOWN
    assert body.velocity == Vector2(0, 0)


@pytest.mark.parametrize(
    "direction, expected",
    [
        pytest.param(Direction.RIGHT, Vector2(5, 0), id="move_right"),
        pytest.param(Direction.LEFT, Vector2(-5, 0), id="move_left"),
        pytest.param(Direction.UP, Vector2(0, -5), id="move_up"),
        pytest.param(Direction.DOWN, Vector2(0, 5), id="move_down"),
    ],
)
def test_move_sets_state_and_velocity(mover, body, direction, expected):
    mover.base_moverate = 5
    mover.move(direction)

    assert mover.state == EntityState.WALKING
    assert body.velocity == expected
    assert mover.facing == direction


def test_move_boundary_case(mover, body):
    mover.base_moverate = 0.0001
    mover.move(Direction.DOWN)

    assert body.velocity == Vector2(0, 0.0001)
    assert mover.facing == Direction.DOWN


def test_stop_resets_velocity_and_state(mover, body):
    mover.base_moverate = 5
    mover.move(Direction.RIGHT)

    mover.stop()

    assert mover.state == EntityState.IDLE
    assert body.velocity == Vector2(0, 0)


def test_facing_persists_after_stop(mover, body):
    mover.move(Direction.RIGHT)
    mover.stop()

    assert mover.facing == Direction.RIGHT


def test_running_sets_state_and_speed(mover, body):
    mover.base_moverate = 5
    mover.move(Direction.UP)

    mover.running()

    assert mover.state == EntityState.RUNNING
    assert mover.base_moverate == CONFIG.player_runrate


def test_walking_resets_state_and_speed(mover, body):
    mover.base_moverate = CONFIG.player_runrate
    mover.move(Direction.LEFT)

    mover.walking()

    assert mover.state == EntityState.WALKING
    assert mover.base_moverate == CONFIG.player_walkrate


def test_jump_sets_state(mover):
    mover.jump()
    assert mover.state == EntityState.JUMPING


def test_jump_blocked_if_already_jumping(mover):
    mover.jump()
    assert mover.state == EntityState.JUMPING

    mover.jump()  # should not change state
    assert mover.state == EntityState.JUMPING


def test_update_movement_state_running(mover, body):
    mover.base_moverate = 5
    mover.move(Direction.RIGHT)

    mover.update_movement_state(running=True)

    assert mover.state == EntityState.RUNNING


def test_update_movement_state_walking(mover, body):
    mover.base_moverate = 5
    mover.move(Direction.RIGHT)

    mover.update_movement_state(running=False)

    assert mover.state == EntityState.WALKING


def test_update_movement_state_idle(mover, body):
    mover.stop()
    mover.update_movement_state(running=True)

    assert mover.state == EntityState.IDLE


def test_set_state_idle_resets_velocity_and_rate(mover, body):
    mover.base_moverate = 10
    mover.move(Direction.RIGHT)

    mover.set_state(EntityState.IDLE)

    assert mover.state == EntityState.IDLE
    assert body.velocity == Vector2(0, 0)
    assert mover.base_moverate == CONFIG.player_walkrate


def test_set_state_same_state_no_change(mover):
    mover.move(Direction.RIGHT)
    assert mover.state == EntityState.WALKING

    mover.set_state(EntityState.WALKING)
    assert mover.state == EntityState.WALKING
