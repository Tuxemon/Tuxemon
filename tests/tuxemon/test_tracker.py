# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from collections.abc import Mapping
from typing import Any

from tuxemon.tracker import (
    TrackingData,
    TrackingPoint,
    decode_tracking,
    encode_tracking,
)


class TestTrackingPoint(unittest.TestCase):
    def test_get_state(self):
        point = TrackingPoint(visited=False)
        self.assertEqual(point.get_state(), {"visited": False})


class TestTrackingData(unittest.TestCase):
    def setUp(self):
        self.tracking_data = TrackingData()
        self.point = TrackingPoint()

    def test_add_location(self):
        self.tracking_data.add_location("loc_1", self.point)
        self.assertIn("loc_1", self.tracking_data.locations)
        self.assertEqual(self.tracking_data.locations["loc_1"], self.point)

    def test_add_duplicate_location(self):
        self.tracking_data.add_location("loc_1", self.point)
        self.tracking_data.add_location("loc_1", self.point)
        self.assertEqual(len(self.tracking_data.locations), 1)

    def test_remove_location(self):
        self.tracking_data.add_location("loc_1", self.point)
        self.tracking_data.remove_location("loc_1")
        self.assertNotIn("loc_1", self.tracking_data.locations)

    def test_remove_non_existent_location(self):
        initial_count = len(self.tracking_data.locations)
        self.tracking_data.remove_location("loc_999")
        self.assertEqual(len(self.tracking_data.locations), initial_count)

    def test_get_location(self):
        self.tracking_data.add_location("loc_1", self.point)
        self.assertEqual(self.tracking_data.get_location("loc_1"), self.point)

    def test_get_non_existent_location(self):
        self.assertIsNone(self.tracking_data.get_location("loc_999"))


class TestEncodingDecoding(unittest.TestCase):
    def test_encode_tracking(self):
        tracking_data = TrackingData()
        tracking_data.add_location("loc_1", TrackingPoint(visited=True))
        tracking_data.add_location("loc_2", TrackingPoint(visited=False))
        encoded = encode_tracking(tracking_data)
        expected = {
            "loc_1": {"visited": True},
            "loc_2": {"visited": False},
        }
        self.assertEqual(encoded, expected)

    def test_decode_tracking(self):
        json_data: Mapping[str, Any] = {
            "loc_1": {"visited": True},
            "loc_2": {"visited": False},
        }
        tracking_data = decode_tracking(json_data)
        self.assertIn("loc_1", tracking_data.locations)
        self.assertIn("loc_2", tracking_data.locations)
        self.assertTrue(tracking_data.get_location("loc_1").visited)
        self.assertFalse(tracking_data.get_location("loc_2").visited)
