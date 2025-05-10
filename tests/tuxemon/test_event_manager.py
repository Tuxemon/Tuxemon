# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import Mock

from tuxemon.event.eventmanager import EventManager
from tuxemon.platform.events import PlayerInput
from tuxemon.state import StateManager


class TestEventManager(unittest.TestCase):

    def test_init(self):
        state_manager = Mock(spec=StateManager)
        event_manager = EventManager(state_manager)
        self.assertEqual(event_manager.state_manager, state_manager)

    def test_process_events(self):
        state_manager = Mock(spec=StateManager)
        event_manager = EventManager(state_manager)

        events = []
        result = list(event_manager.process_events(events))
        self.assertEqual(result, [])

        events = [Mock(spec=PlayerInput), Mock(spec=PlayerInput)]
        state_manager.active_states = []
        result = list(event_manager.process_events(events))
        self.assertEqual(result, events)

        events = [Mock(spec=PlayerInput), Mock(spec=PlayerInput)]
        state = Mock()
        state.process_event = Mock(return_value=Mock(spec=PlayerInput))
        state_manager.active_states = [state]
        result = list(event_manager.process_events(events))
        self.assertEqual(len(result), len(events))

    def test_propagate_event(self):
        state_manager = Mock(spec=StateManager)
        event_manager = EventManager(state_manager)

        event = Mock(spec=PlayerInput)
        state_manager.active_states = []
        result = event_manager.propagate_event(event)
        self.assertEqual(result, event)

        event = Mock(spec=PlayerInput)
        state = Mock()
        state.process_event = Mock(return_value=event)
        state_manager.active_states = [state]
        result = event_manager.propagate_event(event)
        self.assertEqual(result, event)

        event = Mock(spec=PlayerInput)
        processed_event = Mock(spec=PlayerInput)
        state = Mock()
        state.process_event = Mock(return_value=processed_event)
        state_manager.active_states = [state]
        result = event_manager.propagate_event(event)
        self.assertEqual(result, processed_event)

        event = Mock(spec=PlayerInput)
        state = Mock()
        state.process_event = Mock(return_value=None)
        state_manager.active_states = [state]
        result = event_manager.propagate_event(event)
        self.assertIsNone(result)

    def test_release_controls(self):
        state_manager = Mock(spec=StateManager)
        event_manager = EventManager(state_manager)
        input_manager = Mock()
        input_manager.event_queue = Mock()
        input_manager.event_queue.release_controls = Mock(
            return_value=[Mock(spec=PlayerInput), Mock(spec=PlayerInput)]
        )
        state_manager.active_states = []
        result = event_manager.release_controls(input_manager)
        self.assertEqual(
            result,
            list(
                event_manager.process_events(
                    input_manager.event_queue.release_controls.return_value
                )
            ),
        )
