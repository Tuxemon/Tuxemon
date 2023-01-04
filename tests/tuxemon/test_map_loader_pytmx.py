# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from itertools import combinations
from operator import is_not
from unittest.mock import Mock

from tuxemon.map_loader import TMXMapLoader


class TestTMXMapLoaderRegionTiles(unittest.TestCase):
    def setUp(self):
        self.properties = {
            "a": 1,
            "enter": "up",
            "b": 3,
            "exit": "down",
            "continue": "left",
        }
        self.region = Mock(
            x=0,
            y=16,
            width=32,
            height=48,
            properties=self.properties,
        )
        self.grid_size = (16, 16)
        self.result = list(
            TMXMapLoader.region_tiles(self.region, self.grid_size)
        )

    def test_result_is_point_and_properties_tuple(self):
        point = self.result[0][0]
        properties = self.result[0][1]
        self.assertIsInstance(point, tuple)
        self.assertEqual(len(point), 2)
        self.assertIsInstance(properties, dict)

    def test_result_properties_correct(self):
        properties = self.result[0][1]
        expected = {"enter": ["up"], "exit": ["down"], "continue": "left"}
        self.assertEqual(properties, expected)

    def test_result_properties_is_not_same_object_as_input(self):
        properties = self.result[0][1]
        self.assertIsNot(properties, self.properties)

    def test_result_each_properties_are_not_same_object(self):
        properties = [i[1] for i in self.result]
        comps = combinations(properties, 2)
        self.assertTrue(all(is_not(*i) for i in comps))

    def test_correct_result(self):
        # fmt: off
        self.assertEqual(
            [
                ((0, 1), {"enter": ["up"], "exit": ["down"], "continue": "left"}),
                ((1, 1), {"enter": ["up"], "exit": ["down"], "continue": "left"}),
                ((0, 2), {"enter": ["up"], "exit": ["down"], "continue": "left"}),
                ((1, 2), {"enter": ["up"], "exit": ["down"], "continue": "left"}),
                ((0, 3), {"enter": ["up"], "exit": ["down"], "continue": "left"}),
                ((1, 3), {"enter": ["up"], "exit": ["down"], "continue": "left"}),
            ],
            self.result,
        )
