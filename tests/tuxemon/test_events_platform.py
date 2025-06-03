# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import MagicMock

from tuxemon.platform.events import (
    EventQueueHandler,
    InputHandler,
    PlayerInput,
)


class TestInputHandler(unittest.TestCase):

    def setUp(self):
        self.handler = MagicMock(spec=InputHandler)

    def test_press(self):
        self.handler.press = MagicMock(return_value=None)
        self.handler.press(1)
        self.handler.press.assert_called_once_with(1)

    def test_release(self):
        self.handler.release = MagicMock(return_value=None)
        self.handler.release(1)
        self.handler.release.assert_called_once_with(1)

    def test_virtual_stop_events(self):
        self.handler.virtual_stop_events = MagicMock(
            return_value=[PlayerInput(1)]
        )
        events = list(self.handler.virtual_stop_events())
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].button, 1)

    def test_get_events(self):
        self.handler.get_events = MagicMock(return_value=[PlayerInput(1)])
        events = list(self.handler.get_events())
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].button, 1)

    def test_get_events_multiple_frames(self):
        self.handler.get_events = MagicMock(return_value=[PlayerInput(1)])
        events = list(self.handler.get_events())
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].button, 1)
        events = list(self.handler.get_events())
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].button, 1)


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

    def setUp(self):
        self.handler = MagicMock(spec=EventQueueHandler)
        self.input_handler = MagicMock(spec=InputHandler)

    def test_process_events(self):
        self.handler.add_input_handler = MagicMock(return_value=None)
        self.handler.process_events = MagicMock(return_value=[PlayerInput(1)])
        self.handler.add_input_handler(self.input_handler)
        events = list(self.handler.process_events())
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].button, 1)

    def test_release_controls(self):
        self.handler.add_input_handler = MagicMock(return_value=None)
        self.handler.release_controls = MagicMock(
            return_value=[PlayerInput(1)]
        )
        self.handler.add_input_handler(self.input_handler)
        events = list(self.handler.release_controls())
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].button, 1)

    def test_process_events_multiple_frames(self):
        self.handler.add_input_handler = MagicMock(return_value=None)
        self.handler.process_events = MagicMock(return_value=[PlayerInput(1)])
        self.handler.add_input_handler(self.input_handler)
        events = list(self.handler.process_events())
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].button, 1)
        events = list(self.handler.process_events())
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].button, 1)

    def test_process_events_multiple_handlers(self):
        self.handler.add_input_handler = MagicMock(return_value=None)
        self.handler.process_events = MagicMock(
            return_value=[PlayerInput(1), PlayerInput(2)]
        )
        self.handler.add_input_handler(self.input_handler)
        self.handler.add_input_handler(self.input_handler)
        events = list(self.handler.process_events())
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0].button, 1)
        self.assertEqual(events[1].button, 2)

    def test_release_controls_multiple_handlers(self):
        self.handler.add_input_handler = MagicMock(return_value=None)
        self.handler.release_controls = MagicMock(
            return_value=[PlayerInput(1), PlayerInput(2)]
        )
        self.handler.add_input_handler(self.input_handler)
        self.handler.add_input_handler(self.input_handler)
        events = list(self.handler.release_controls())
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0].button, 1)
        self.assertEqual(events[1].button, 2)
