# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from pathlib import Path

from tuxemon.map_loader import YAMLEventLoader, parse_yaml


class TestYAMLEventLoader(unittest.TestCase):

    def setUp(self):
        self.loader = YAMLEventLoader()
        self.valid_yaml_path = (
            Path("tests/tuxemon") / "test_event_loader_map.yaml"
        )

    def test_parse_yaml_success(self):
        result = parse_yaml(self.valid_yaml_path)
        self.assertIsInstance(result, dict)
        self.assertIn("events", result)

    def test_load_events(self):
        result = self.loader.load_events(self.valid_yaml_path, "event")
        self.assertIn("event", result)
        self.assertIsInstance(result["event"], list)
        self.assertGreater(len(result["event"]), 0)
        event = result["event"][0]
        self.assertEqual(event.name, "test_event")
        self.assertEqual(event.x, 1)
        self.assertEqual(event.y, 2)

    def test_load_collision(self):
        result = self.loader.load_collision(self.valid_yaml_path)
        self.assertIn((2, 4), result)
        self.assertIn((3, 5), result)
        self.assertIsNone(result[(2, 4)])
