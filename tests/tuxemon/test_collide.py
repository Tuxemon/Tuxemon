# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest

from tuxemon.event import MapCondition, collide


class TestCollide(unittest.TestCase):
    def test_tile_inside_condition(self):
        condition = MapCondition(
            type="",
            parameters=[],
            x=0,
            y=0,
            width=5,
            height=5,
            operator="",
            name=None,
        )
        tile_position = (2, 2)
        self.assertTrue(collide(condition, tile_position))

    def test_tile_outside_condition(self):
        condition = MapCondition(
            type="",
            parameters=[],
            x=0,
            y=0,
            width=5,
            height=5,
            operator="",
            name=None,
        )
        tile_position = (6, 6)
        self.assertFalse(collide(condition, tile_position))

    def test_tile_on_edge_condition(self):
        condition = MapCondition(
            type="",
            parameters=[],
            x=0,
            y=0,
            width=5,
            height=5,
            operator="",
            name=None,
        )
        tile_position = (0, 0)  # Top-left corner
        self.assertTrue(collide(condition, tile_position))
        tile_position = (4, 4)  # Bottom-right corner
        self.assertTrue(collide(condition, tile_position))

    def test_invalid_tile_position(self):
        condition = MapCondition(
            type="",
            parameters=[],
            x=0,
            y=0,
            width=5,
            height=5,
            operator="",
            name=None,
        )
        tile_position = "invalid"
        with self.assertRaises(TypeError):
            collide(condition, tile_position)

    def test_edge_cases_for_condition_dimensions(self):
        condition = MapCondition(
            type="",
            parameters=[],
            x=0,
            y=0,
            width=0,
            height=0,
            operator="",
            name=None,
        )
        tile_position = (0, 0)
        self.assertFalse(collide(condition, tile_position))

        condition = MapCondition(
            type="",
            parameters=[],
            x=0,
            y=0,
            width=1,
            height=1,
            operator="",
            name=None,
        )
        tile_position = (0, 0)
        self.assertTrue(collide(condition, tile_position))

    def test_negative_coordinates(self):
        condition = MapCondition(
            type="",
            parameters=[],
            x=-2,
            y=-2,
            width=5,
            height=5,
            operator="",
            name=None,
        )
        tile_position = (0, 0)
        self.assertTrue(collide(condition, tile_position))

    def test_large_coordinates(self):
        condition = MapCondition(
            type="",
            parameters=[],
            x=10000,
            y=10000,
            width=5,
            height=5,
            operator="",
            name=None,
        )
        tile_position = (10001, 10001)
        self.assertTrue(collide(condition, tile_position))

    def test_edge_cases_zero_width_or_height(self):
        condition = MapCondition(
            type="",
            parameters=[],
            x=0,
            y=0,
            width=0,
            height=5,
            operator="",
            name=None,
        )
        tile_position = (0, 0)
        self.assertFalse(collide(condition, tile_position))

        condition = MapCondition(
            type="",
            parameters=[],
            x=0,
            y=0,
            width=5,
            height=0,
            operator="",
            name=None,
        )
        tile_position = (0, 0)
        self.assertFalse(collide(condition, tile_position))
