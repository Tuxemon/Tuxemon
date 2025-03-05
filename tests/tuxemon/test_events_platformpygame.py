# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import Mock

import pygame as pg

from tuxemon import graphics, prepare
from tuxemon.platform.const import buttons, events
from tuxemon.platform.events import PlayerInput
from tuxemon.platform.platform_pygame.events import (
    HORIZONTAL_AXIS,
    VERTICAL_AXIS,
    PygameGamepadInput,
    PygameKeyboardInput,
    PygameMouseInput,
    PygameTouchOverlayInput,
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


class TestPygameMouseInput(unittest.TestCase):

    def setUp(self):
        pg.init()
        self.mouse_input = PygameMouseInput()
        self.mouse_input.buttons[buttons.MOUSELEFT] = PlayerInput(
            buttons.MOUSELEFT
        )

    def tearDown(self):
        pg.quit()

    def test_mouse_button_down(self):
        event = pg.event.Event(pg.MOUSEBUTTONDOWN, button=1, pos=(10, 20))
        self.mouse_input.process_event(event)
        self.assertTrue(self.mouse_input.buttons[buttons.MOUSELEFT].pressed)
        self.assertEqual(
            self.mouse_input.buttons[buttons.MOUSELEFT].value, (10, 20)
        )

    def test_mouse_button_up(self):
        event_down = pg.event.Event(pg.MOUSEBUTTONDOWN, button=1, pos=(10, 20))
        self.mouse_input.process_event(event_down)
        event_up = pg.event.Event(pg.MOUSEBUTTONUP, button=1, pos=(10, 20))
        self.mouse_input.process_event(event_up)
        self.assertFalse(self.mouse_input.buttons[buttons.MOUSELEFT].pressed)

    def test_other_mouse_buttons(self):
        event = pg.event.Event(pg.MOUSEBUTTONDOWN, button=3, pos=(50, 60))
        self.mouse_input.process_event(event)
        self.assertTrue(self.mouse_input.buttons[buttons.MOUSELEFT].pressed)

        event2 = pg.event.Event(pg.MOUSEBUTTONUP, button=3, pos=(50, 60))
        self.mouse_input.process_event(event2)
        self.assertFalse(self.mouse_input.buttons[buttons.MOUSELEFT].pressed)


class TestPygameKeyboardInput(unittest.TestCase):

    def setUp(self):
        pg.init()
        self.keyboard_input = PygameKeyboardInput()
        self.keyboard_input.buttons[buttons.UP] = PlayerInput(buttons.UP)
        self.keyboard_input.buttons[buttons.A] = PlayerInput(buttons.A)
        self.keyboard_input.buttons[events.UNICODE] = PlayerInput(
            events.UNICODE
        )

    def tearDown(self):
        pg.quit()

    def test_key_press(self):
        event = pg.event.Event(pg.KEYDOWN, key=pg.K_UP)
        self.keyboard_input.process_event(event)
        self.assertTrue(self.keyboard_input.buttons[buttons.UP].pressed)

    def test_key_release(self):
        event_down = pg.event.Event(pg.KEYDOWN, key=pg.K_UP)
        self.keyboard_input.process_event(event_down)
        event_up = pg.event.Event(pg.KEYUP, key=pg.K_UP)
        self.keyboard_input.process_event(event_up)
        self.assertFalse(self.keyboard_input.buttons[buttons.UP].pressed)

    def test_mapped_key(self):
        event = pg.event.Event(pg.KEYDOWN, key=pg.K_RETURN)
        self.keyboard_input.process_event(event)
        self.assertTrue(self.keyboard_input.buttons[buttons.A].pressed)

    def test_unicode_input(self):
        event = pg.event.Event(pg.KEYDOWN, unicode="a", key=pg.K_a)
        self.keyboard_input.process_event(event)
        self.assertTrue(self.keyboard_input.buttons[events.UNICODE].pressed)
        self.assertEqual(
            self.keyboard_input.buttons[events.UNICODE].value, "a"
        )
        event_up = pg.event.Event(pg.KEYUP, key=pg.K_a)
        self.keyboard_input.process_event(event_up)
        self.assertFalse(self.keyboard_input.buttons[events.UNICODE].pressed)

    def test_unmapped_key(self):
        # Testing a key that is not in the default_input_map or a unicode value.
        event = pg.event.Event(pg.KEYDOWN, key=pg.K_F1)
        self.keyboard_input.process_event(event)
        # It should not trigger any of the mapped buttons.
        self.assertFalse(self.keyboard_input.buttons[buttons.UP].pressed)
        self.assertFalse(self.keyboard_input.buttons[buttons.A].pressed)
        self.assertFalse(self.keyboard_input.buttons[events.UNICODE].pressed)

    def test_modifier_keys(self):
        event = pg.event.Event(pg.KEYDOWN, key=pg.K_RSHIFT)
        self.keyboard_input.process_event(event)
        self.assertTrue(self.keyboard_input.buttons[buttons.B].pressed)

        event2 = pg.event.Event(pg.KEYUP, key=pg.K_RSHIFT)
        self.keyboard_input.process_event(event2)
        self.assertFalse(self.keyboard_input.buttons[buttons.B].pressed)

        event3 = pg.event.Event(pg.KEYDOWN, key=pg.K_LSHIFT)
        self.keyboard_input.process_event(event3)
        self.assertTrue(self.keyboard_input.buttons[buttons.B].pressed)

        event4 = pg.event.Event(pg.KEYUP, key=pg.K_LSHIFT)
        self.keyboard_input.process_event(event4)
        self.assertFalse(self.keyboard_input.buttons[buttons.B].pressed)


class TestPygameTouchOverlayInput(unittest.TestCase):

    def setUp(self):
        pg.init()
        pg.display.set_mode((0, 0))
        prepare.SCREEN_SIZE = (800, 600)
        self.touch_input = PygameTouchOverlayInput(128)
        self.touch_input.buttons[buttons.UP] = PlayerInput(buttons.UP)
        self.touch_input.buttons[buttons.DOWN] = PlayerInput(buttons.DOWN)
        self.touch_input.buttons[buttons.LEFT] = PlayerInput(buttons.LEFT)
        self.touch_input.buttons[buttons.RIGHT] = PlayerInput(buttons.RIGHT)
        self.touch_input.buttons[buttons.A] = PlayerInput(buttons.A)
        self.touch_input.buttons[buttons.B] = PlayerInput(buttons.B)

        # Mock the graphics.load_and_scale function
        def mock_load_and_scale(filename):
            return pg.Surface((50, 50))  # Return a dummy surface

        graphics.load_and_scale = mock_load_and_scale

        self.touch_input.load()

    def tearDown(self):
        pg.quit()
        prepare.SCREEN_SIZE = (0, 0)

    def test_touch_dpad_up(self):
        up_rect = self.touch_input.ui.dpad["rect"]["up"]
        event = pg.event.Event(
            pg.MOUSEBUTTONDOWN, button=1, pos=up_rect.center
        )
        self.touch_input.process_event(event)
        self.assertTrue(self.touch_input.buttons[buttons.UP].pressed)

    def test_touch_dpad_down(self):
        down_rect = self.touch_input.ui.dpad["rect"]["down"]
        event = pg.event.Event(
            pg.MOUSEBUTTONDOWN, button=1, pos=down_rect.center
        )
        self.touch_input.process_event(event)
        self.assertTrue(self.touch_input.buttons[buttons.DOWN].pressed)

    def test_touch_dpad_left(self):
        left_rect = self.touch_input.ui.dpad["rect"]["left"]
        event = pg.event.Event(
            pg.MOUSEBUTTONDOWN, button=1, pos=left_rect.center
        )
        self.touch_input.process_event(event)
        self.assertTrue(self.touch_input.buttons[buttons.LEFT].pressed)

    def test_touch_dpad_right(self):
        right_rect = self.touch_input.ui.dpad["rect"]["right"]
        event = pg.event.Event(
            pg.MOUSEBUTTONDOWN, button=1, pos=right_rect.center
        )
        self.touch_input.process_event(event)
        self.assertTrue(self.touch_input.buttons[buttons.RIGHT].pressed)

    def test_touch_a_button(self):
        a_rect = self.touch_input.ui.a_button["rect"]
        event = pg.event.Event(pg.MOUSEBUTTONDOWN, button=1, pos=a_rect.center)
        self.touch_input.process_event(event)
        self.assertTrue(self.touch_input.buttons[buttons.A].pressed)

    def test_touch_b_button(self):
        b_rect = self.touch_input.ui.b_button["rect"]
        event = pg.event.Event(pg.MOUSEBUTTONDOWN, button=1, pos=b_rect.center)
        self.touch_input.process_event(event)
        self.assertTrue(self.touch_input.buttons[buttons.B].pressed)

    def test_touch_release(self):
        up_rect = self.touch_input.ui.dpad["rect"]["up"]
        event_down = pg.event.Event(
            pg.MOUSEBUTTONDOWN, button=1, pos=up_rect.center
        )
        self.touch_input.process_event(event_down)
        event_up = pg.event.Event(
            pg.MOUSEBUTTONUP, button=1, pos=up_rect.center
        )
        self.touch_input.process_event(event_up)
        self.assertFalse(self.touch_input.buttons[buttons.UP].pressed)

    def test_touch_outside_buttons(self):
        event = pg.event.Event(pg.MOUSEBUTTONDOWN, button=1, pos=(10, 10))
        self.touch_input.process_event(event)
        self.assertFalse(
            any(button.pressed for button in self.touch_input.buttons.values())
        )
