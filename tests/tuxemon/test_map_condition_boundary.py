# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest

from tuxemon.boundary import Dimensions, MapConditionBoundary
from tuxemon.db import BoundingBox, Operator, SpatialCondition


class TestMapConditionBoundary(unittest.TestCase):
    def test_tile_inside_condition(self):
        box = BoundingBox(x=0, y=0, width=5, height=5)
        condition = SpatialCondition(
            type="",
            parameters=[],
            box=box,
            operator=Operator.IS,
            name="unknown",
        )
        boundary = MapConditionBoundary(condition)
        self.assertTrue(boundary.is_within((2, 2)))

    def test_tile_outside_condition(self):
        box = BoundingBox(x=0, y=0, width=5, height=5)
        condition = SpatialCondition(
            type="",
            parameters=[],
            box=box,
            operator=Operator.IS,
            name="unknown",
        )
        boundary = MapConditionBoundary(condition)
        self.assertFalse(boundary.is_within((6, 6)))

    def test_tile_on_edge_condition(self):
        box = BoundingBox(x=0, y=0, width=5, height=5)
        condition = SpatialCondition(
            type="",
            parameters=[],
            box=box,
            operator=Operator.IS,
            name="unknown",
        )
        boundary = MapConditionBoundary(condition)
        self.assertTrue(boundary.is_within((0, 0)))  # Top-left
        self.assertTrue(boundary.is_within((4, 4)))  # Bottom-right

    def test_invalid_tile_position(self):
        box = BoundingBox(x=0, y=0, width=5, height=5)
        condition = SpatialCondition(
            type="",
            parameters=[],
            box=box,
            operator=Operator.IS,
            name="unknown",
        )
        boundary = MapConditionBoundary(condition)
        with self.assertRaises(TypeError):
            boundary.is_within("invalid")

    def test_edge_cases_for_condition_dimensions(self):
        box = BoundingBox(x=0, y=0, width=1, height=1)
        condition = SpatialCondition(
            type="",
            parameters=[],
            box=box,
            operator=Operator.IS,
            name="unknown",
        )
        boundary = MapConditionBoundary(condition)
        self.assertFalse(boundary.is_within((1, 1)))

        box = BoundingBox(x=0, y=0, width=1, height=1)
        condition = SpatialCondition(
            type="",
            parameters=[],
            box=box,
            operator=Operator.IS,
            name="unknown",
        )
        boundary = MapConditionBoundary(condition)
        self.assertTrue(boundary.is_within((0, 0)))

    def test_negative_coordinates(self):
        box = BoundingBox(x=-2, y=-2, width=5, height=5)
        condition = SpatialCondition(
            type="",
            parameters=[],
            box=box,
            operator=Operator.IS,
            name="unknown",
        )
        boundary = MapConditionBoundary(condition)
        self.assertTrue(boundary.is_within((0, 0)))

    def test_large_coordinates(self):
        box = BoundingBox(x=10000, y=10000, width=5, height=5)
        condition = SpatialCondition(
            type="",
            parameters=[],
            box=box,
            operator=Operator.IS,
            name="unknown",
        )
        boundary = MapConditionBoundary(condition)
        self.assertTrue(boundary.is_within((10001, 10001)))

    def test_edge_cases_zero_width_or_height(self):
        box = BoundingBox(x=0, y=0, width=1, height=5)
        condition = SpatialCondition(
            type="",
            parameters=[],
            box=box,
            operator=Operator.IS,
            name="unknown",
        )
        boundary = MapConditionBoundary(condition)
        self.assertFalse(boundary.is_within((1, 1)))

        box = BoundingBox(x=0, y=0, width=5, height=1)
        condition = SpatialCondition(
            type="",
            parameters=[],
            box=box,
            operator=Operator.IS,
            name="unknown",
        )
        boundary = MapConditionBoundary(condition)
        self.assertFalse(boundary.is_within((1, 1)))

    def test_move_shifts_boundary_position(self):
        box = BoundingBox(x=0, y=0, width=5, height=5)
        condition = SpatialCondition(
            type="",
            parameters=[],
            box=box,
            operator=Operator.IS,
            name="unknown",
        )
        boundary = MapConditionBoundary(condition)
        self.assertTrue(boundary.is_within((2, 2)))

        boundary.move(3, 3)
        self.assertFalse(boundary.is_within((2, 2)))
        self.assertTrue(boundary.is_within((5, 5)))
        self.assertEqual(boundary.get_center(), (5.5, 5.5))

    def test_resize_expands_boundary(self):
        box = BoundingBox(x=0, y=0, width=2, height=2)
        condition = SpatialCondition(
            type="",
            parameters=[],
            box=box,
            operator=Operator.IS,
            name="unknown",
        )
        boundary = MapConditionBoundary(condition)
        self.assertFalse(boundary.is_within((3, 3)))

        boundary.resize(2, 2)
        self.assertTrue(boundary.is_within((3, 3)))
        self.assertEqual(
            boundary.get_dimensions(), Dimensions(width=4.0, height=4.0)
        )

    def test_resize_contracts_boundary(self):
        box = BoundingBox(x=0, y=0, width=5, height=5)
        condition = SpatialCondition(
            type="",
            parameters=[],
            box=box,
            operator=Operator.IS,
            name="unknown",
        )
        boundary = MapConditionBoundary(condition)
        self.assertTrue(boundary.is_within((4, 4)))

        boundary.resize(-3, -3)
        self.assertFalse(boundary.is_within((4, 4)))
        self.assertEqual(
            boundary.get_dimensions(), Dimensions(width=2.0, height=2.0)
        )

    def test_resize_to_zero_dimensions(self):
        box = BoundingBox(x=0, y=0, width=2, height=2)
        condition = SpatialCondition(
            type="",
            parameters=[],
            box=box,
            operator=Operator.IS,
            name="unknown",
        )
        boundary = MapConditionBoundary(condition)
        boundary.resize(-2, -2)
        self.assertFalse(boundary.is_within((0, 0)))
        self.assertEqual(
            boundary.get_dimensions(), Dimensions(width=0.0, height=0.0)
        )

    def test_move_and_resize_combination(self):
        box = BoundingBox(x=0, y=0, width=3, height=3)
        condition = SpatialCondition(
            type="",
            parameters=[],
            box=box,
            operator=Operator.IS,
            name="unknown",
        )
        boundary = MapConditionBoundary(condition)
        boundary.move(2, 2)
        boundary.resize(2, 2)
        self.assertTrue(boundary.is_within((4, 4)))
        self.assertFalse(boundary.is_within((1, 1)))
        self.assertEqual(boundary.get_center(), (4.5, 4.5))
