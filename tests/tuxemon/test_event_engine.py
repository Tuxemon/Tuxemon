# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import Mock

from tuxemon.client import LocalPygameClient
from tuxemon.event.eventengine import EventEngine
from tuxemon.map_manager import MapManager
from tuxemon.session import Session, local_session


class TestEventEngine(unittest.TestCase):
    def setUp(self):
        self.eng = EventEngine(local_session)

    def test_init(self):
        self.assertIsNone(self.eng.current_map)
        self.assertEqual(self.eng.running_events, {})
        self.assertEqual(self.eng.partial_events, [])

    def test_reset(self):
        self.eng.running_events = {1: "event1", 2: "event2"}
        self.eng.current_map = "map1"
        self.eng.timer = 10.0
        self.eng.wait = 5.0
        self.eng.reset()
        self.assertIsNone(self.eng.current_map)
        self.assertEqual(self.eng.running_events, {})
        self.assertEqual(self.eng.timer, 0.0)
        self.assertEqual(self.eng.wait, 0.0)

    def test_get_action(self):
        self.eng.actions = {"action1": lambda: "action1"}
        self.assertEqual(self.eng.get_action("action1"), "action1")
        self.assertIsNone(self.eng.get_action("action2"))

    def test_get_condition(self):
        self.eng.conditions = {"condition1": Mock()}
        self.eng.conditions["condition1"].test = Mock(return_value=True)
        self.assertIsNotNone(self.eng.get_condition("condition1"))
        self.assertIsNone(self.eng.get_condition("condition2"))

    def test_start_event(self):
        class EventObject:
            def __init__(self, id):
                self.id = id

        event = EventObject(1)
        self.eng.session = Mock(spec=Session)
        self.eng.session.client = Mock(spec=LocalPygameClient)
        self.eng.session.client.map_manager = Mock(spec=MapManager)
        self.eng.session.client.map_manager.inits = []
        self.eng.start_event(event)
        self.assertIn(1, self.eng.running_events)
