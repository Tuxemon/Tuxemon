# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from tuxemon.map_loader import EventLoader, YAMLEventLoader


class TestEventLoader(unittest.TestCase):

    def setUp(self):
        self.event_loader = EventLoader()
        self.yaml_loader = YAMLEventLoader()
        self.event_loader.yaml_loader = self.yaml_loader

    @patch.object(YAMLEventLoader, "load_collision")
    def test_load_collision_events_success(self, mock_load_collision):
        yaml_file = Path("test.yaml")
        mock_load_collision.return_value = {(1, 2): None}
        result = self.event_loader.load_collision_events(yaml_file)
        self.assertEqual(result, {(1, 2): None})
        mock_load_collision.assert_called_once_with(yaml_file.as_posix())

    @patch.object(YAMLEventLoader, "load_collision")
    def test_load_collision_events_failure(self, mock_load_collision):
        yaml_file = Path("test.yaml")
        mock_load_collision.side_effect = Exception("Test error")
        result = self.event_loader.load_collision_events(yaml_file)
        self.assertEqual(result, {})
        mock_load_collision.assert_called_once_with(yaml_file.as_posix())

    @patch.object(YAMLEventLoader, "load_events")
    def test_load_specific_events_success(self, mock_load_events):
        yaml_file = Path("test.yaml")
        event_type = "event"
        mock_load_events.return_value = {event_type: [Mock()]}
        result = self.event_loader.load_specific_events(yaml_file, event_type)
        self.assertEqual(len(result), 1)
        mock_load_events.assert_called_once_with(
            yaml_file.as_posix(), event_type
        )

    @patch.object(YAMLEventLoader, "load_events")
    def test_load_specific_events_failure(self, mock_load_events):
        yaml_file = Path("test.yaml")
        event_type = "event"
        mock_load_events.side_effect = Exception("Test error")
        result = self.event_loader.load_specific_events(yaml_file, event_type)
        self.assertEqual(result, [])
        mock_load_events.assert_called_once_with(
            yaml_file.as_posix(), event_type
        )

    @patch.object(YAMLEventLoader, "load_events")
    def test_load_specific_events_empty(self, mock_load_events):
        yaml_file = Path("test.yaml")
        event_type = "event"
        mock_load_events.return_value = {}
        result = self.event_loader.load_specific_events(yaml_file, event_type)
        self.assertEqual(result, [])
        mock_load_events.assert_called_once_with(
            yaml_file.as_posix(), event_type
        )
