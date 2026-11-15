# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import Mock

import pytest

from tuxemon.camera.camera import CameraTracker
from tuxemon.math import Vector2


@pytest.fixture
def tracker():
    view = Mock()
    view.get_size = Mock(return_value=(100, 80))
    view.screen_size = (100, 80)
    view.position = Vector2(50, 40)
    view.get_center = lambda pos: pos
    entity = Mock()
    entity.position = Vector2(10, 20)
    return CameraTracker(view, entity)


def test_initial_state(tracker):
    assert tracker.follows_entity
    assert not tracker.is_moving_smoothly
    assert isinstance(tracker.entity, Mock)


def test_update_centers_on_entity(tracker):
    tracker.entity.position = Vector2(30, 40)
    tracker.update(0.1)
    assert tracker.view.position == Vector2(30, 40)


def test_update_returns_zero_vector(tracker):
    result = tracker.update(0.1)
    assert result == Vector2(0, 0)


def test_update_calls_smooth_transition_when_flag_set(tracker):
    tracker.is_moving_smoothly = True
    tracker._update_smooth_transition = Mock()
    tracker.update(0.1)
    tracker._update_smooth_transition.assert_called_once_with(0.1)


def test_set_entity_with_reset_snaps_camera(tracker):
    new_entity = Mock()
    new_entity.position = Vector2(99, 77)
    tracker.set_entity(new_entity, reset=True)
    assert tracker.view.position == Vector2(99, 77)


def test_move_smoothly_to_sets_target_and_speed(tracker):
    target = Vector2(200, 200)
    tracker.view.position = Vector2(0, 0)
    tracker.move_smoothly_to(target, duration=2.0)
    assert tracker.is_moving_smoothly
    assert tracker.target_position == target
    assert tracker.transition_speed > 0
