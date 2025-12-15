# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import pytest

from tuxemon import prepare
from tuxemon.camera.camera import CameraView, project
from tuxemon.math import Vector2


@pytest.fixture
def view():
    tile_size = prepare.TILE_SIZE
    screen_size = prepare.SCREEN_SIZE
    return CameraView(tile_size=tile_size, screen_size=screen_size)


def assert_vector_equal(actual: Vector2, expected: Vector2):
    assert actual.x == expected.x
    assert actual.y == expected.y


def test_initial_position(view):
    assert_vector_equal(view.position, Vector2(0, 0))


def test_set_position(view):
    target = Vector2(1.0, 1.0)
    projected = project((target.x, target.y))
    expected = Vector2(
        projected[0] + view.tile_size[0] // 2,
        projected[1] + view.tile_size[1] // 2,
    )
    view.set_position(target.x, target.y)
    assert_vector_equal(view.position, expected)


def test_move_relative(view):
    view.position = Vector2(50, 50)
    view.move(dx=10, dy=-20)
    assert_vector_equal(view.position, Vector2(60, 30))


def test_get_center_origin(view):
    projected = project((0.0, 0.0))
    expected = Vector2(
        projected[0] + view.tile_size[0] // 2,
        projected[1] + view.tile_size[1] // 2,
    )
    result = view.get_center(Vector2(0.0, 0.0))
    assert_vector_equal(result, expected)


def test_get_center_whole_tile(view):
    position = Vector2(2.0, 3.0)
    projected = project((position.x, position.y))
    expected = Vector2(
        projected[0] + view.tile_size[0] // 2,
        projected[1] + view.tile_size[1] // 2,
    )
    result = view.get_center(position)
    assert_vector_equal(result, expected)


def test_get_center_fractional_tile(view):
    position = Vector2(0.5, 0.5)
    projected = project((position.x, position.y))
    expected = Vector2(
        projected[0] + view.tile_size[0] // 2,
        projected[1] + view.tile_size[1] // 2,
    )
    result = view.get_center(position)
    assert_vector_equal(result, expected)


def test_get_center_negative_coordinates(view):
    position = Vector2(-1.0, -1.0)
    projected = project((position.x, position.y))
    expected = Vector2(
        projected[0] + view.tile_size[0] // 2,
        projected[1] + view.tile_size[1] // 2,
    )
    result = view.get_center(position)
    assert_vector_equal(result, expected)


def test_get_center_large_coordinates(view):
    position = Vector2(100.0, 200.0)
    projected = project((position.x, position.y))
    expected = Vector2(
        projected[0] + view.tile_size[0] // 2,
        projected[1] + view.tile_size[1] // 2,
    )
    result = view.get_center(position)
    assert_vector_equal(result, expected)


def test_get_center_zero_tile_size():
    screen_size = prepare.SCREEN_SIZE
    view = CameraView(tile_size=(0, 0), screen_size=screen_size)
    projected = project((1.0, 1.0))
    expected = Vector2(projected[0], projected[1])
    result = view.get_center(Vector2(1.0, 1.0))
    assert_vector_equal(result, expected)


def test_get_center_extreme_tile_size():
    screen_size = prepare.SCREEN_SIZE
    tile_size = (1024, 512)
    view = CameraView(tile_size=tile_size, screen_size=screen_size)
    projected = project((1.0, 1.0))
    expected = Vector2(
        projected[0] + tile_size[0] // 2,
        projected[1] + tile_size[1] // 2,
    )
    result = view.get_center(Vector2(1.0, 1.0))
    assert_vector_equal(result, expected)
