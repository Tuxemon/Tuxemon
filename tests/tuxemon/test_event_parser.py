# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest

from tuxemon.db import BoundingBox, EventObject
from tuxemon.map.map_loader import EventParser


class TestEventParser(unittest.TestCase):
    def setUp(self):
        self.parser = EventParser()
        self.event_data = {
            "behav": ["walk:north"],
            "conditions": ["is flag quest_started"],
            "actions": ["set flag quest_completed"],
        }
        self.name = "test_event"
        self.box = BoundingBox(x=5, y=10, width=2, height=3)

    def test_create_event_object(self):
        event = self.parser.create_event_object(
            self.event_data,
            self.name,
            self.box,
        )

        # Basic structure
        self.assertIsInstance(event, EventObject)
        self.assertEqual(event.name, self.name)
        self.assertEqual(event.box.x, self.box.x)
        self.assertEqual(len(event.conds), 2)  # 1 behav + 1 condition
        self.assertEqual(len(event.acts), 2)  # 1 behav + 1 action

        # Check behavior condition
        behav_cond = event.conds[0]
        self.assertEqual(behav_cond.type, "behav")
        self.assertEqual(behav_cond.parameters, ["walk:north"])
        self.assertEqual(behav_cond.operator, "is")

        # Check behavior action
        behav_act = event.acts[0]
        self.assertEqual(behav_act.type, "behav")
        self.assertEqual(behav_act.parameters, ["walk:north"])

        # Check parsed condition
        cond = event.conds[1]
        self.assertEqual(cond.type, "flag")
        self.assertEqual(cond.parameters, ["quest_started"])
        self.assertEqual(cond.operator, "is")

        # Check parsed action
        act = event.acts[1]
        self.assertEqual(act.type, "set")
        self.assertEqual(act.parameters, ["flag quest_completed"])

    def test_empty_event_data(self):
        event = self.parser.create_event_object({}, self.name, self.box)
        self.assertEqual(len(event.conds), 0)
        self.assertEqual(len(event.acts), 0)

    def test_behav_only(self):
        data = {"behav": ["run:east"]}
        event = self.parser.create_event_object(data, self.name, self.box)
        self.assertEqual(len(event.conds), 1)
        self.assertEqual(len(event.acts), 1)
        self.assertEqual(event.conds[0].parameters, ["run:east"])
        self.assertEqual(event.acts[0].parameters, ["run:east"])

    def test_malformed_condition(self):
        data = {"conditions": ["is"]}
        with self.assertRaises(ValueError):
            self.parser.create_event_object(
                data,
                self.name,
                self.box,
            )

    def test_multiple_behaviors(self):
        data = {"behav": ["jump:up", "slide:left"]}
        event = self.parser.create_event_object(data, self.name, self.box)
        self.assertEqual(len(event.conds), 2)
        self.assertEqual(len(event.acts), 2)
        self.assertEqual(event.conds[0].name, "behav20")
        self.assertEqual(event.conds[1].name, "behav10")

    def test_complex_action(self):
        data = {"actions": ["set flag quest_completed:true"]}
        event = self.parser.create_event_object(data, self.name, self.box)
        self.assertEqual(
            event.acts[0].parameters, ["flag quest_completed:true"]
        )

    def test_event_object_integrity(self):
        event = self.parser.create_event_object(
            self.event_data,
            self.name,
            self.box,
        )
        self.assertTrue(hasattr(event, "id"))
        self.assertEqual(event.name, "test_event")
        self.assertEqual(event.box.x, self.box.x)
        self.assertEqual(event.box.y, self.box.y)

    def test_event_with_timeout_and_delay(self):
        data = {"timeout": 5, "delay": 2}
        event = self.parser.create_event_object(
            data,
            self.name,
            self.box,
            priority=0,
            timeout=5.0,
            delay=2.0,
        )
        self.assertEqual(event.timeout, 5.0)
        self.assertEqual(event.delay, 2.0)

    def test_event_defaults(self):
        event = self.parser.create_event_object({}, self.name, self.box)
        self.assertIsNone(event.timeout)
        self.assertIsNone(event.delay)

    def test_condition_with_not_operator(self):
        data = {"conditions": ["not flag quest_started"]}
        event = self.parser.create_event_object(data, self.name, self.box)
        cond = event.conds[0]
        self.assertEqual(cond.operator, "not")

    def test_event_box_integrity(self):
        event = self.parser.create_event_object(
            self.event_data, self.name, self.box
        )
        self.assertEqual(event.box.width, 2)
        self.assertEqual(event.box.height, 3)

    def test_multiple_actions(self):
        data = {
            "actions": ["set flag quest_started", "clear flag quest_completed"]
        }
        event = self.parser.create_event_object(data, self.name, self.box)
        self.assertEqual(len(event.acts), 2)
        self.assertEqual(event.acts[0].type, "set")
        self.assertEqual(event.acts[1].type, "clear")
