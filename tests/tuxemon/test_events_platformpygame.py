# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import Mock

import pygame as pg

from tuxemon.platform.const import buttons
from tuxemon.platform.platform_pygame.events import (
    HORIZONTAL_AXIS,
    VERTICAL_AXIS,
    PygameGamepadInput,
)


class TestPygameGamepadInput(unittest.TestCase):

    def setUp(self):
        if not pg.get_init():
            pg.init()
        self.event_map = {
            0: buttons.A,
            1: buttons.B,
            6: buttons.BACK,
            11: buttons.LEFT,
            12: buttons.RIGHT,
            13: buttons.UP,
            14: buttons.DOWN,
            7: buttons.START,
        }
        self.gamepad_input = PygameGamepadInput(
            event_map=self.event_map, deadzone=0.2
        )
        self.gamepad_input.press = Mock()
        self.gamepad_input.release = Mock()

    def tearDown(self):
        pg.quit()

    def test_is_within_deadzone(self):
        self.assertTrue(self.gamepad_input.is_within_deadzone(0.1))
        self.assertFalse(self.gamepad_input.is_within_deadzone(0.3))

    def test_handle_button_press(self):
        self.gamepad_input.handle_button(buttons.A, True)
        self.gamepad_input.press.assert_called_once_with(buttons.A, 0.0)

    def test_handle_button_release(self):
        self.gamepad_input.handle_button(buttons.A, False)
        self.gamepad_input.release.assert_called_once_with(buttons.A)

    def test_check_button_press(self):
        event = pg.event.Event(pg.JOYBUTTONDOWN, button=0)
        self.gamepad_input.check_button(event)
        self.gamepad_input.press.assert_called_once_with(buttons.A, 0.0)

    def test_check_button_release(self):
        event = pg.event.Event(pg.JOYBUTTONUP, button=0)
        self.gamepad_input.check_button(event)
        self.gamepad_input.release.assert_called_once_with(buttons.A)

    def test_check_axis_horizontal_right(self):
        event = pg.event.Event(
            pg.JOYAXISMOTION, axis=HORIZONTAL_AXIS, value=0.5
        )
        self.gamepad_input.check_axis(event)
        self.gamepad_input.press.assert_called_with(buttons.RIGHT, 0.5)

    def test_check_axis_horizontal_left(self):
        event = pg.event.Event(
            pg.JOYAXISMOTION, axis=HORIZONTAL_AXIS, value=-0.5
        )
        self.gamepad_input.check_axis(event)
        self.gamepad_input.press.assert_called_with(buttons.LEFT, 0.5)

    def test_check_axis_vertical_down(self):
        event = pg.event.Event(pg.JOYAXISMOTION, axis=VERTICAL_AXIS, value=0.5)
        self.gamepad_input.check_axis(event)
        self.gamepad_input.press.assert_called_with(buttons.DOWN, 0.5)

    def test_check_axis_vertical_up(self):
        event = pg.event.Event(
            pg.JOYAXISMOTION, axis=VERTICAL_AXIS, value=-0.5
        )
        self.gamepad_input.check_axis(event)
        self.gamepad_input.press.assert_called_with(buttons.UP, 0.5)

    def test_check_axis_deadzone(self):
        event = pg.event.Event(
            pg.JOYAXISMOTION, axis=HORIZONTAL_AXIS, value=0.1
        )
        self.gamepad_input.check_axis(event)
        self.gamepad_input.release.assert_any_call(buttons.LEFT)
        self.gamepad_input.release.assert_any_call(buttons.RIGHT)

        event = pg.event.Event(pg.JOYAXISMOTION, axis=VERTICAL_AXIS, value=0.1)
        self.gamepad_input.check_axis(event)
        self.gamepad_input.release.assert_any_call(buttons.UP)
        self.gamepad_input.release.assert_any_call(buttons.DOWN)
