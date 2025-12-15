# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import MagicMock

from tuxemon.client import LocalPygameClient
from tuxemon.db import BoundingBox, EventObject
from tuxemon.event.eventaction import ActionManager
from tuxemon.event.eventengine import EventEngine
from tuxemon.event.running import ConditionEvaluator
from tuxemon.map.map_manager import MapManager
from tuxemon.session import Session, local_session


class TestEventEngine(unittest.TestCase):
    def setUp(self):
        self.box = BoundingBox(x=0, y=0, width=1, height=1)
        action = MagicMock(spec=ActionManager)
        evaluator = MagicMock(spec=ConditionEvaluator)
        self.eng = EventEngine(local_session, action, evaluator)

    def test_init(self):
        self.assertIsNone(self.eng.current_map)
        self.assertEqual(self.eng.running_events, {})
        self.assertEqual(self.eng.partial_events, [])

    def test_reset(self):
        self.eng.running_events = {1: "event1", 2: "event2"}
        self.eng.current_map = "map1"
        self.eng.reset()
        self.assertIsNone(self.eng.current_map)
        self.assertEqual(self.eng.running_events, {})

    def test_start_event(self):
        event = EventObject(
            id=1,
            name="",
            priority=0,
            box=self.box,
            conds=[],
            acts=[],
        )
        self.eng.session = MagicMock(spec=Session)
        self.eng.session.client = MagicMock(spec=LocalPygameClient)
        self.eng.session.client.map_manager = MagicMock(spec=MapManager)
        self.eng.session.client.map_manager.inits = []
        self.eng.start_event(event)
        self.assertIn(1, self.eng.running_events)

    def test_register_global_event_prevents_duplicates(self):
        event = EventObject(
            id=99,
            name="",
            priority=0,
            box=self.box,
            conds=[],
            acts=[],
        )
        self.eng.global_events = [event]
        result = self.eng.register_global_event(event)
        self.assertFalse(result)

    def test_unregister_global_event_removes_event(self):
        event = EventObject(
            id=77,
            name="",
            priority=0,
            box=self.box,
            conds=[],
            acts=[],
        )
        self.eng.global_events = [event]
        self.eng.triggered_global_events = {77}

        result = self.eng.unregister_global_event(77)

        self.assertTrue(result)
        self.assertNotIn(event, self.eng.global_events)
        self.assertNotIn(77, self.eng.triggered_global_events)

    def test_register_global_event_prevents_duplicates(self):
        event = EventObject(
            id=303,
            name="",
            priority=0,
            box=self.box,
            conds=[],
            acts=[],
        )
        self.eng.global_events = [event]
        result = self.eng.register_global_event(event)
        self.assertFalse(result)
        self.assertEqual(len(self.eng.global_events), 1)

    def test_unregister_global_event_removes_event_and_flag(self):
        event = EventObject(
            id=404,
            name="",
            priority=0,
            box=self.box,
            conds=[],
            acts=[],
        )
        self.eng.global_events = [event]
        self.eng.triggered_global_events = {404}

        result = self.eng.unregister_global_event(404)

        self.assertTrue(result)
        self.assertNotIn(event, self.eng.global_events)
        self.assertNotIn(404, self.eng.triggered_global_events)
