# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import Mock

import pytest

from tuxemon.camera.camera import Camera, CameraController, CameraManager
from tuxemon.prepare import DISPLAY_CONTEXT


@pytest.fixture
def manager():
    return CameraManager()


@pytest.fixture
def context():
    return DISPLAY_CONTEXT


@pytest.fixture
def cameras():
    return Mock(spec=Camera), Mock(spec=Camera)


@pytest.fixture
def input_event():
    return Mock()


def test_add_camera_sets_active_if_none(manager, cameras):
    camera1, _ = cameras
    manager.add_camera("cam1", camera1)
    assert "cam1" in manager.cameras
    assert manager.active_camera == camera1
    assert isinstance(manager.controller, CameraController)


def test_add_camera_does_not_override_active(manager, cameras):
    camera1, camera2 = cameras
    manager.add_camera("cam1", camera1)
    manager.add_camera("cam2", camera2)
    assert manager.active_camera == camera1


def test_set_active_camera_switches_control(manager, cameras):
    camera1, camera2 = cameras
    manager.add_camera("cam1", camera1)
    manager.add_camera("cam2", camera2)
    manager.set_active_camera("cam2")
    assert manager.active_camera == camera2
    assert isinstance(manager.controller, CameraController)
    assert manager.controller.camera == camera2


def test_set_active_camera_raises_if_unmanaged(manager):
    with pytest.raises(ValueError):
        manager.set_active_camera("camX")


def test_update_calls_active_camera_update(manager, cameras):
    camera1, _ = cameras
    manager.add_camera("cam1", camera1)
    manager.update(0.1)
    camera1.update.assert_called_once_with(0.1)


def test_handle_input_delegates_to_controller(manager, cameras, input_event):
    camera1, _ = cameras
    manager.add_camera("cam1", camera1)
    manager.controller.handle_input = Mock(return_value=input_event)
    result = manager.handle_input(input_event)
    manager.controller.handle_input.assert_called_once_with(input_event)
    assert result == input_event


def test_handle_input_returns_none_if_no_controller(manager, input_event):
    result = manager.handle_input(input_event)
    assert result is None


def test_get_active_camera_returns_correct_camera(manager, cameras):
    camera1, _ = cameras
    manager.add_camera("cam1", camera1)
    assert manager.get_active_camera() == camera1


def test_remove_nonexistent_camera_raises(manager):
    with pytest.raises(ValueError):
        manager.remove_camera("camX")


def test_remove_inactive_camera_leaves_active_intact(manager, cameras):
    camera1, camera2 = cameras
    manager.add_camera("cam1", camera1)
    manager.add_camera("cam2", camera2)
    manager.remove_camera("cam2")
    assert manager.get_active_camera() == camera1


def test_remove_active_camera_clears_active(manager, cameras):
    camera1, _ = cameras
    manager.add_camera("cam1", camera1)
    manager.remove_camera("cam1")
    assert manager.get_active_camera() is None
    assert manager.controller is None


def test_remove_active_camera_with_multiple_then_clear(manager, cameras):
    camera1, camera2 = cameras
    manager.add_camera("cam1", camera1)
    manager.add_camera("cam2", camera2)
    manager.remove_camera("cam1")
    assert manager.get_active_camera() is None
    assert manager.controller is None
    manager.set_active_camera("cam2")
    assert manager.get_active_camera() == camera2


def test_integration_add_and_switch_real_cameras(context):
    player = Mock()
    boundary = Mock()
    camera1 = Camera(player, boundary, context)
    camera2 = Camera(player, boundary, context)
    manager = CameraManager()

    manager.add_camera("cam1", camera1)
    manager.add_camera("cam2", camera2)

    assert manager.get_active_camera() == camera1

    manager.set_active_camera("cam2")
    assert manager.get_active_camera() == camera2
    assert isinstance(manager.controller, CameraController)
    assert manager.controller.camera == camera2


def test_stress_add_and_remove_many_cameras(manager):
    for i in range(100):
        cam = Mock(spec=Camera)
        manager.add_camera(f"cam{i}", cam)

    assert len(manager.cameras) == 100

    for i in range(100):
        manager.remove_camera(f"cam{i}")

    assert len(manager.cameras) == 0
    assert manager.get_active_camera() is None
    assert manager.controller is None
