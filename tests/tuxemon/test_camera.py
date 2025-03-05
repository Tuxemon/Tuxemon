# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import Mock

from tuxemon import prepare
from tuxemon.camera import (
    SPEED_DOWN,
    SPEED_LEFT,
    SPEED_RIGHT,
    SPEED_UP,
    Camera,
    CameraInputHandler,
    CameraManager,
    project,
    unproject,
)
from tuxemon.math import Vector2
from tuxemon.platform.const import intentions

# For the entity at position (5.0, 5.0):
# The project function calculates:
# cx = int(5.0 * 16) = 80
# cy = int(5.0 * 16) = 80
# Then, get_center adds half the tile size to both cx and cy:
# cx + self.tile_size[0] // 2 = 80 + 8 = 88
# cy + self.tile_size[1] // 2 = 80 + 8 = 88


class TestCamera(unittest.TestCase):

    def setUp(self):
        prepare.TILE_SIZE = (16, 16)
        self.entity = Mock()
        self.entity.position3 = Vector2(5.0, 5.0)
        self.boundary = Mock()
        self.boundary.get_boundary_validity.return_value = (True, True)
        self.camera = Camera(self.entity, self.boundary)

    def test_project(self):
        self.assertEqual(project((1.0, 2.0)), (16, 32))
        self.assertEqual(project((0.5, 0.5)), (8, 8))

    def test_unproject(self):
        self.assertEqual(unproject((16, 32)), (1, 2))
        self.assertEqual(unproject((8, 8)), (0, 0))

    def test_get_center(self):
        self.assertEqual(
            self.camera.get_center(Vector2(5.0, 5.0)), Vector2(88, 88)
        )

    def test_get_entity_center(self):
        self.assertEqual(self.camera.get_entity_center(), Vector2(88, 88))

    def test_update_follow(self):
        self.camera.update()
        self.assertEqual(self.camera.position, Vector2(88, 88))

    def test_update_unfollow(self):
        self.camera.update()
        self.camera.unfollow()
        self.camera.update()
        self.assertEqual(self.camera.position, Vector2(88, 88))
        self.camera.move(dx=10)
        self.assertNotEqual(self.camera.position, Vector2(88, 88))

    def test_move_absolute(self):
        self.camera.set_position(x=10.0, y=10.0)
        self.assertEqual(self.camera.position, Vector2(168, 168))

    def test_move_relative_valid(self):
        self.boundary.get_boundary_validity.return_value = (True, True)
        self.camera.move(dx=16, dy=16)
        self.assertEqual(self.camera.position, Vector2(104, 104))

    def test_move_relative_invalid_x(self):
        self.boundary.get_boundary_validity.return_value = (False, True)
        self.camera.move(dx=16, dy=16)
        self.assertEqual(self.camera.position, Vector2(88, 104))

    def test_move_relative_invalid_y(self):
        self.boundary.get_boundary_validity.return_value = (True, False)
        self.camera.move(dx=16, dy=16)
        self.assertEqual(self.camera.position, Vector2(104, 88))

    def test_reset_to_entity_center(self):
        self.camera.move(dx=10, dy=10)
        self.camera.reset_to_entity_center()
        self.assertEqual(self.camera.position, Vector2(88, 88))
        self.assertTrue(self.camera.follows_entity)
        self.assertFalse(self.camera.free_roaming_enabled)

    def test_switch_to_entity(self):
        new_entity = Mock()
        new_entity.position3 = Vector2(10.0, 10.0)
        self.camera.switch_to_entity(new_entity)
        self.assertEqual(self.camera.entity, new_entity)
        self.assertEqual(self.camera.position, Vector2(168, 168))
        self.assertTrue(self.camera.follows_entity)

    def test_switch_to_original_entity(self):
        new_entity = Mock()
        new_entity.position3 = Vector2(10.0, 10.0)
        self.camera.switch_to_entity(new_entity)
        self.camera.switch_to_original_entity()
        self.assertEqual(self.camera.entity, self.entity)
        self.assertEqual(self.camera.position, Vector2(88, 88))
        self.assertTrue(self.camera.follows_entity)

    def test_move_up(self):
        self.camera.move_up()
        self.assertEqual(self.camera.position.y, 88 - SPEED_UP)

    def test_move_down(self):
        self.camera.move_down()
        self.assertEqual(self.camera.position.y, 88 + SPEED_DOWN)

    def test_move_left(self):
        self.camera.move_left()
        self.assertEqual(self.camera.position.x, 88 - SPEED_LEFT)

    def test_move_right(self):
        self.camera.move_right()
        self.assertEqual(self.camera.position.x, 88 + SPEED_RIGHT)


class TestCameraManager(unittest.TestCase):
    def setUp(self):
        self.manager = CameraManager()
        self.camera1 = Mock(spec=Camera)
        self.camera2 = Mock(spec=Camera)

    def test_add_camera(self):
        self.manager.add_camera(self.camera1)
        self.assertIn(self.camera1, self.manager.cameras)
        self.assertEqual(self.manager.active_camera, self.camera1)

    def test_set_active_camera(self):
        self.manager.add_camera(self.camera1)
        self.manager.add_camera(self.camera2)
        self.manager.set_active_camera(self.camera2)
        self.assertEqual(self.manager.active_camera, self.camera2)

    def test_update(self):
        self.manager.add_camera(self.camera1)
        self.manager.update()
        self.camera1.update.assert_called_once()

    def test_handle_input(self):
        self.manager.add_camera(self.camera1)
        self.camera1.free_roaming_enabled = True
        event = Mock()
        self.manager.input_handler.handle_input = Mock()
        self.manager.handle_input(event)
        self.manager.input_handler.handle_input.assert_called_once_with(event)

    def test_get_active_camera(self):
        self.manager.add_camera(self.camera1)
        self.assertEqual(self.manager.get_active_camera(), self.camera1)


class TestCameraInputHandler(unittest.TestCase):
    def setUp(self):
        self.camera = Mock(spec=Camera)
        self.handler = CameraInputHandler(self.camera)

    def test_handle_input_free_roaming_held_up(self):
        self.camera.free_roaming_enabled = True
        event = Mock()
        event.held = True
        event.pressed = False
        event.button = intentions.UP
        self.handler.handle_input(event)
        self.camera.move_up.assert_called_once()

    def test_handle_input_free_roaming_pressed_down(self):
        self.camera.free_roaming_enabled = True
        event = Mock()
        event.held = False
        event.pressed = True
        event.button = intentions.DOWN
        self.handler.handle_input(event)
        self.camera.move_down.assert_called_once()

    def test_handle_input_free_roaming_disabled(self):
        self.camera.free_roaming_enabled = False
        event = Mock()
        event.held = True
        event.button = intentions.UP
        self.handler.handle_input(event)
        self.camera.move_up.assert_not_called()

    def test_handle_input_return_event(self):
        self.camera.free_roaming_enabled = True
        event = Mock()
        event.held = True
        event.button = intentions.UP
        returned_event = self.handler.handle_input(event)
        self.assertEqual(event, returned_event)

    def test_handle_input_left(self):
        self.camera.free_roaming_enabled = True
        event = Mock()
        event.held = True
        event.button = intentions.LEFT
        self.handler.handle_input(event)
        self.camera.move_left.assert_called_once()

    def test_handle_input_right(self):
        self.camera.free_roaming_enabled = True
        event = Mock()
        event.held = True
        event.button = intentions.RIGHT
        self.handler.handle_input(event)
        self.camera.move_right.assert_called_once()
