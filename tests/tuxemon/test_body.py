# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import pytest

from tuxemon.db import Direction
from tuxemon.entity.entity import Body, Mover
from tuxemon.math import Vector2


@pytest.fixture
def body():
    return Body(position=Vector2(0, 0))


@pytest.fixture
def mover(body):
    return Mover(body)


def test_initialization(body, mover):
    assert body.position == Vector2(0, 0)
    assert body.velocity == Vector2(0, 0)
    assert body.acceleration == Vector2(0, 0)
    assert mover.facing == Direction.DOWN


@pytest.mark.parametrize(
    "velocity,acceleration,dt,expected_pos,expected_vel",
    [
        pytest.param(
            Vector2(1, 1),
            Vector2(1, 0),
            1.0,
            Vector2(2, 1),
            Vector2(2, 1),
            id="basic_acceleration",
        ),
        pytest.param(
            Vector2(5, 5),
            Vector2(0, 0),
            0.0,
            Vector2(0, 0),
            Vector2(5, 5),
            id="zero_dt",
        ),
        pytest.param(
            Vector2(999999, 999999),
            Vector2(0, 0),
            1.0,
            Vector2(999999, 999999),
            Vector2(999999, 999999),
            id="large_values",
        ),
        pytest.param(
            Vector2(1, 1),
            Vector2(0, 0),
            1000.0,
            Vector2(1000, 1000),
            Vector2(1, 1),
            id="large_dt",
        ),
    ],
)
def test_update_position(
    body, velocity, acceleration, dt, expected_pos, expected_vel
):
    body.velocity = velocity
    body.acceleration = acceleration
    body.update(dt)

    assert body.position == expected_pos
    assert body.velocity == expected_vel


def test_reset_selective(body):
    body.position = Vector2(10, 10)
    body.velocity = Vector2(5, 5)
    body.acceleration = Vector2(1, 1)

    body.reset(
        reset_position=False,
        reset_velocity=True,
        reset_acceleration=False,
    )

    assert body.position == Vector2(10, 10)
    assert body.velocity == Vector2(0, 0)
    assert body.acceleration == Vector2(1, 1)


def test_reset_all(body):
    body.position = Vector2(15, 20)
    body.velocity = Vector2(10, 15)
    body.acceleration = Vector2(5, 5)

    body.reset()

    assert body.position == Vector2(0, 0)
    assert body.velocity == Vector2(0, 0)
    assert body.acceleration == Vector2(0, 0)


def test_stop_sets_velocity_to_zero(body, mover):
    body.velocity = Vector2(5, 5)
    mover.stop()
    assert body.velocity == Vector2(0, 0)


@pytest.mark.parametrize(
    "direction,expected",
    [
        pytest.param(Direction.UP, Vector2(0, -5), id="up"),
        pytest.param(Direction.DOWN, Vector2(0, 5), id="down"),
        pytest.param(Direction.LEFT, Vector2(-5, 0), id="left"),
        pytest.param(Direction.RIGHT, Vector2(5, 0), id="right"),
    ],
)
def test_move_with_valid_direction(mover, body, direction, expected):
    mover.base_moverate = 5
    mover.moverate_modifier = 1.0

    mover.move(direction)

    assert body.velocity == expected
    assert mover.facing == direction


def test_move_boundary_case(mover, body):
    mover.base_moverate = 0.0001
    mover.moverate_modifier = 1.0

    mover.move(Direction.DOWN)

    assert body.velocity == Vector2(0, 0.0001)
    assert mover.facing == Direction.DOWN


def test_facing_persists_after_stop(mover, body):
    mover.base_moverate = 5
    mover.move(Direction.RIGHT)
    mover.stop()

    assert body.velocity == Vector2(0, 0)
    assert mover.facing == Direction.RIGHT
