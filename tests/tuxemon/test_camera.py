# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import Mock

import pytest
from pygame.rect import Rect

from tuxemon.camera.camera import Camera, project, unproject
from tuxemon.math import Vector2
from tuxemon.prepare import DISPLAY_CONTEXT


@pytest.fixture
def context():
    return DISPLAY_CONTEXT


@pytest.fixture
def camera_setup(context):
    context.tile_size = (16, 16)
    entity = Mock()
    entity.position = Vector2(5.0, 5.0)
    boundary = Mock()
    boundary.get_boundary_validity.return_value = (True, True)
    camera = Camera(entity, boundary, context)
    camera.reset_to_entity_center()
    projected = project(context, (entity.position.x, entity.position.y))
    expected_center = Vector2(
        projected[0] + context.tile_size[0] // 2,
        projected[1] + context.tile_size[1] // 2,
    )
    return camera, entity, boundary, expected_center


def assert_vector_equal(actual: Vector2, expected: Vector2):
    assert actual.x == expected.x
    assert actual.y == expected.y


def test_update_calls_tracker_and_effects(camera_setup):
    camera, _, _, _ = camera_setup
    camera.tracker.update = Mock(return_value=Vector2(0, 0))
    camera.effects.update = Mock()
    camera.update(0.1)
    camera.tracker.update.assert_called_once_with(0.1)
    camera.effects.update.assert_called_once()


def test_move_valid(camera_setup):
    camera, _, _, _ = camera_setup
    camera.update(0.1)
    camera.move(dx=16, dy=16)
    assert camera.get_position() == Vector2(104, 104)


def test_move_invalid_x(camera_setup):
    camera, _, boundary, _ = camera_setup
    boundary.get_boundary_validity.return_value = (False, True)
    camera.update(0.1)
    camera.move(dx=16, dy=16)
    assert camera.get_position() == Vector2(88, 104)


def test_move_invalid_y(camera_setup):
    camera, _, boundary, _ = camera_setup
    boundary.get_boundary_validity.return_value = (True, False)
    camera.update(0.1)
    camera.move(dx=16, dy=16)
    assert camera.get_position() == Vector2(104, 88)


def test_is_following(camera_setup):
    camera, _, _, _ = camera_setup
    assert camera.is_following()
    camera.unfollow()
    assert not camera.is_following()


def test_set_position(camera_setup):
    camera, _, _, _ = camera_setup
    camera.set_position(10.0, 10.0)
    assert camera.get_position() == Vector2(168, 168)


def test_follow_and_unfollow(camera_setup):
    camera, _, _, _ = camera_setup
    camera.unfollow()
    assert not camera.is_following()
    camera.follow()
    assert camera.is_following()


def test_move_up(camera_setup):
    camera, _, _, _ = camera_setup
    camera.update(0.1)
    camera.move(dx=0, dy=-5)
    assert camera.get_position().y == 88 - 5


def test_move_down(camera_setup):
    camera, _, _, _ = camera_setup
    camera.update(0.1)
    camera.move(dx=0, dy=5)
    assert camera.get_position().y == 88 + 5


def test_move_left(camera_setup):
    camera, _, _, _ = camera_setup
    camera.update(0.1)
    camera.move(dx=-5, dy=0)
    assert camera.get_position().x == 88 - 5


def test_move_right(camera_setup):
    camera, _, _, _ = camera_setup
    camera.update(0.1)
    camera.move(dx=5, dy=0)
    assert camera.get_position().x == 88 + 5


def test_shake_triggers_effect(camera_setup):
    camera, _, _, _ = camera_setup
    camera.effects.shake = Mock()
    camera.shake(2.0, 1.0)
    camera.effects.shake.assert_called_once_with(2.0, 1.0)


def test_smooth_reset_to_entity_center(camera_setup):
    camera, entity, _, _ = camera_setup
    camera.tracker.move_smoothly_to = Mock()
    camera.smooth_reset_to_entity_center(duration=1.0)
    camera.tracker.move_smoothly_to.assert_called_once_with(
        Vector2(5.0, 5.0), 1.0
    )
    assert camera.tracker.pending_follow


def test_switch_entity_to_new(camera_setup):
    camera, _, _, _ = camera_setup
    new_entity = Mock()
    new_entity.position = Vector2(10.0, 10.0)
    camera.switch_entity(new_entity)
    assert camera.tracker.entity == new_entity
    assert camera.is_following()


def test_switch_entity_to_original(camera_setup):
    camera, entity, _, _ = camera_setup
    new_entity = Mock()
    new_entity.position = Vector2(10.0, 10.0)
    camera.switch_entity(new_entity)
    camera.switch_entity()
    assert camera.tracker.entity == entity
    assert camera.is_following()


def test_reset_to_entity_center(camera_setup):
    camera, _, _, expected_center = camera_setup
    camera.move(dx=10, dy=10)
    camera.reset_to_entity_center()
    assert camera.get_position() == expected_center
    assert camera.is_following()
    assert not camera.free_roaming_enabled


def test_move_smoothly_to(camera_setup):
    camera, _, _, _ = camera_setup
    camera.tracker.move_smoothly_to = Mock()
    camera.move_smoothly_to(100.0, 200.0, duration=2.0)
    camera.tracker.move_smoothly_to.assert_called_once_with(
        Vector2(100.0, 200.0), 2.0
    )


def test_get_position(camera_setup):
    camera, _, _, expected_center = camera_setup
    camera.update(0.1)
    assert camera.get_position() == expected_center


def test_get_viewport_returns_rect(camera_setup):
    camera, _, _, _ = camera_setup
    viewport = camera.get_viewport()
    assert isinstance(viewport, Rect)


def test_viewport_center_matches_expected(camera_setup):
    camera, _, _, expected_center = camera_setup
    camera.update(0.0)
    viewport = camera.get_viewport()
    center = Vector2(viewport.center)
    assert_vector_equal(center, expected_center)


def test_viewport_top_left_calculation(camera_setup):
    camera, _, _, expected_center = camera_setup
    camera.update(0.0)
    width, height = camera.view.get_size()
    expected_top_left = expected_center - Vector2(width // 2, height // 2)
    viewport = camera.get_viewport()
    assert viewport.topleft == (
        int(expected_top_left.x),
        int(expected_top_left.y),
    )


@pytest.mark.parametrize(
    "coords, expected",
    [
        pytest.param((0.0, 0.0), (0, 0), id="origin"),
        pytest.param((-1.0, -2.0), (-16, -32), id="negative_coords"),
        pytest.param((0.25, 0.75), (4, 12), id="fractional_coords"),
        pytest.param((100.0, 200.0), (1600, 3200), id="large_coords"),
    ],
)
def test_project(coords, expected, context):
    assert project(context, coords) == expected


@pytest.mark.parametrize(
    "pixels, expected",
    [
        pytest.param((0, 0), (0, 0), id="origin"),
        pytest.param((-16, -32), (-1, -2), id="negative_pixels"),
        pytest.param((4, 12), (0, 0), id="fractional_back_to_origin"),
        pytest.param((1600, 3200), (100, 200), id="large_pixels"),
    ],
)
def test_unproject(pixels, expected, context):
    assert unproject(context, pixels) == expected


def test_project_unproject_round_trip(context):
    original = (7.5, 3.25)
    projected = project(context, original)
    unprojected = unproject(context, projected)
    assert unprojected == (7, 3)
