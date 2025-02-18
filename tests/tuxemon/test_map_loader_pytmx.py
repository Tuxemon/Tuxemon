# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from itertools import combinations
from operator import is_not
from unittest.mock import Mock

from tuxemon.db import Direction as Dir
from tuxemon.map import RegionProperties as RP
from tuxemon.map_loader import TMXMapLoader


class TestTMXMapLoaderRegionTiles(unittest.TestCase):
    def setUp(self):
        self.properties = {
            "a": 1,
            "enter_from": Dir.up,
            "b": 3,
            "exit_from": Dir.down,
            "endure": Dir.left,
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
        if properties:
            self.assertIsInstance(properties, RP)

    def test_result_properties_correct(self):
        properties = self.result[0][1]
        expected = RP(
            enter_from=[Dir.up],
            exit_from=[Dir.down],
            endure=[Dir.left],
            entity=None,
            key=None,
        )
        if properties:
            self.assertEqual(properties, expected)

    def test_result_properties_is_not_same_object_as_input(self):
        properties = self.result[0][1]
        self.assertIsNot(properties, self.properties)

    def test_result_each_properties_are_not_same_object(self):
        properties = [i[1] for i in self.result if i[1]]
        comps = combinations(properties, 2)
        self.assertTrue(all(is_not(*i) for i in comps))

    def test_correct_result(self):
        # fmt: off
        self.assertEqual(
            [
                ((0, 1), RP([Dir.up], [Dir.down], [Dir.left], None, None)),
                ((1, 1), RP([Dir.up], [Dir.down], [Dir.left], None, None)),
                ((0, 2), RP([Dir.up], [Dir.down], [Dir.left], None, None)),
                ((1, 2), RP([Dir.up], [Dir.down], [Dir.left], None, None)),
                ((0, 3), RP([Dir.up], [Dir.down], [Dir.left], None, None)),
                ((1, 3), RP([Dir.up], [Dir.down], [Dir.left], None, None)),
            ],
            self.result,
        )
