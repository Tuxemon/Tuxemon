# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import pytest

from tuxemon.camera.camera import CameraView, project
from tuxemon.math import Vector2
from tuxemon.prepare import DISPLAY_CONTEXT, DisplayContext
from tuxemon.scaling import DefaultScaling


@pytest.fixture
def context():
    return DISPLAY_CONTEXT


@pytest.fixture
def view(context):
    return CameraView(context)


@pytest.fixture
def center(context):
    def compute(position: Vector2, tile_size):
        px, py = project(context, (position.x, position.y))
        return Vector2(px + tile_size[0] // 2, py + tile_size[1] // 2)

    return compute


def assert_vector_equal(actual: Vector2, expected: Vector2):
    assert actual.x == expected.x
    assert actual.y == expected.y


def test_initial_position(view):
    assert_vector_equal(view.position, Vector2(0, 0))


def test_set_position(view, center):
    target = Vector2(1.0, 1.0)
    expected = center(target, view.tile_size)
    view.set_position(target.x, target.y)
    assert_vector_equal(view.position, expected)


def test_move_relative(view):
    view.position = Vector2(50, 50)
    view.move(dx=10, dy=-20)
    assert_vector_equal(view.position, Vector2(60, 30))


def test_get_center_origin(view, center):
    expected = center(Vector2(0.0, 0.0), view.tile_size)
    result = view.get_center(Vector2(0.0, 0.0))
    assert_vector_equal(result, expected)


def test_get_center_whole_tile(view, center):
    position = Vector2(2.0, 3.0)
    expected = center(position, view.tile_size)
    result = view.get_center(position)
    assert_vector_equal(result, expected)


def test_get_center_fractional_tile(view, center):
    position = Vector2(0.5, 0.5)
    expected = center(position, view.tile_size)
    result = view.get_center(position)
    assert_vector_equal(result, expected)


def test_get_center_negative_coordinates(view, center):
    position = Vector2(-1.0, -1.0)
    expected = center(position, view.tile_size)
    result = view.get_center(position)
    assert_vector_equal(result, expected)


def test_get_center_large_coordinates(view, center):
    position = Vector2(100.0, 200.0)
    expected = center(position, view.tile_size)
    result = view.get_center(position)
    assert_vector_equal(result, expected)


def test_get_center_zero_tile_size(context):
    fake_context = DisplayContext(
        screen=context.screen,
        rect=context.rect,
        tile_size=(0, 0),
        scaling=DefaultScaling(1),
        scale=1,
        resolution=(1, 1),
    )
    view = CameraView(fake_context)
    px, py = project(fake_context, (1.0, 1.0))
    expected = Vector2(px, py)
    result = view.get_center(Vector2(1.0, 1.0))
    assert_vector_equal(result, expected)


def test_get_center_extreme_tile_size(context):
    tile_size = (1024, 512)
    fake_context = DisplayContext(
        screen=context.screen,
        rect=context.rect,
        tile_size=tile_size,
        scaling=DefaultScaling(1),
        scale=1,
        resolution=(1, 1),
    )
    view = CameraView(fake_context)
    px, py = project(fake_context, (1.0, 1.0))
    expected = Vector2(px + tile_size[0] // 2, py + tile_size[1] // 2)
    result = view.get_center(Vector2(1.0, 1.0))
    assert_vector_equal(result, expected)
