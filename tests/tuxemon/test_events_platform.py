# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest

from tuxemon.platform.events import (
    EventQueueHandler,
    InputHandler,
    PlayerInput,
)


class MockInputHandler(InputHandler):
    def __init__(self):
        self.events = []
        self.buttons = {1: PlayerInput(1), 2: PlayerInput(2)}

    def process_event(self, event):
        self.events.append(event)

    def get_events(self):
        yield from self.buttons.values()

    def virtual_stop_events(self):
        yield from [PlayerInput(b, 0) for b in self.buttons]


class MockEventQueueHandler(EventQueueHandler):
    def __init__(self):
        self._inputs = {}
        self.processed_events = []

    def add_input_handler(self, handler):
        self._inputs[1] = [handler]

    def process_events(self):
        for handlers in self._inputs.values():
            for handler in handlers:
                for event in handler.get_events():
                    self.processed_events.append(event)
                    yield event

    def release_controls(self):
        released = []
        for handlers in self._inputs.values():
            for handler in handlers:
                released.extend(list(handler.virtual_stop_events()))
        return released


class TestInputHandler(unittest.TestCase):
    def test_press(self):
        handler = MockInputHandler()
        handler.press(1)
        self.assertEqual(handler.buttons[1].value, 1.0)
        self.assertEqual(handler.buttons[1].hold_time, 1)
        self.assertFalse(handler.buttons[1].triggered)

    def test_release(self):
        handler = MockInputHandler()
        handler.press(1)
        handler.release(1)
        self.assertEqual(handler.buttons[1].value, 0.0)
        self.assertEqual(handler.buttons[1].hold_time, 0)
        self.assertTrue(handler.buttons[1].triggered)

    def test_get_events(self):
        handler = MockInputHandler()
        handler.press(1)
        events = list(handler.get_events())
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0].button, 1)
        self.assertEqual(events[0].value, 1.0)
        self.assertEqual(events[0].hold_time, 1)
        self.assertFalse(events[0].triggered)

    def test_virtual_stop_events(self):
        handler = MockInputHandler()
        handler.press(1)
        events = list(handler.virtual_stop_events())
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0].button, 1)
        self.assertEqual(events[0].value, 0)

    def test_press_release_press(self):
        handler = MockInputHandler()
        handler.press(1)
        handler.release(1)
        handler.press(1)
        self.assertEqual(handler.buttons[1].value, 1.0)
        self.assertEqual(handler.buttons[1].hold_time, 1)
        self.assertTrue(handler.buttons[1].triggered)

    def test_press_hold_release(self):
        handler = MockInputHandler()
        handler.press(1)
        handler.get_events()
        handler.release(1)
        self.assertEqual(handler.buttons[1].value, 0.0)
        self.assertEqual(handler.buttons[1].hold_time, 0)
        self.assertTrue(handler.buttons[1].triggered)


class TestPlayerInput(unittest.TestCase):
    def test_pressed(self):
        input = PlayerInput(1, 1.0, 1)
        self.assertTrue(input.pressed)

    def test_held(self):
        input = PlayerInput(1, 1.0, 2)
        self.assertTrue(input.held)

    def test_not_pressed(self):
        input = PlayerInput(1, 0.0, 1)
        self.assertFalse(input.pressed)

    def test_not_held(self):
        input = PlayerInput(1, 1.0, 0)
        self.assertTrue(input.held)

    def test_triggered(self):
        input = PlayerInput(1, 1.0, 1)
        self.assertFalse(input.triggered)

    def test_not_triggered(self):
        input = PlayerInput(1, 1.0, 2)
        input.triggered = False
        self.assertFalse(input.triggered)


class TestEventQueueHandler(unittest.TestCase):
    def test_process_events(self):
        handler = MockEventQueueHandler()
        input_handler = MockInputHandler()
        handler.add_input_handler(input_handler)
        input_handler.press(1)
        events = list(handler.process_events())
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0].button, 1)
        self.assertEqual(events[0].value, 1.0)
        self.assertEqual(events[0].hold_time, 1)
        self.assertFalse(events[0].triggered)

    def test_release_controls(self):
        handler = MockEventQueueHandler()
        input_handler = MockInputHandler()
        handler.add_input_handler(input_handler)
        input_handler.press(1)
        events = list(handler.release_controls())
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0].button, 1)
        self.assertEqual(events[0].value, 0)

    def test_process_events_multiple_handlers(self):
        handler = MockEventQueueHandler()
        input_handler1 = MockInputHandler()
        input_handler2 = MockInputHandler()
        handler.add_input_handler(input_handler1)
        handler.add_input_handler(input_handler2)
        input_handler1.press(1)
        input_handler2.press(2)
        events = list(handler.process_events())
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0].button, 1)
        self.assertEqual(events[1].value, 1)
        self.assertEqual(events[0].hold_time, 0)
        self.assertFalse(events[0].triggered)
        self.assertEqual(events[1].button, 2)
        self.assertEqual(events[1].value, 1.0)
        self.assertEqual(events[1].hold_time, 1)
        self.assertFalse(events[1].triggered)

    def test_process_events_multiple_frames(self):
        handler = MockEventQueueHandler()
        input_handler = MockInputHandler()
        handler.add_input_handler(input_handler)
        input_handler.press(1)
        events = list(handler.process_events())
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0].button, 1)
        self.assertEqual(events[0].value, 1.0)
        self.assertEqual(events[0].hold_time, 1)
        self.assertFalse(events[0].triggered)
        input_handler.get_events()
        events = list(handler.process_events())
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0].button, 1)
        self.assertEqual(events[0].value, 1.0)
        self.assertEqual(events[0].hold_time, 1)
        self.assertFalse(events[0].triggered)
