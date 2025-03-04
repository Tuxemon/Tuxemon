# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest

from tuxemon.boundary import BoundaryChecker


class TestBoundaryChecker(unittest.TestCase):
    def setUp(self):
        self.checker = BoundaryChecker()

    def test_initial_boundaries(self):
        self.assertEqual(self.checker.invalid_x, (-1, 0))
        self.assertEqual(self.checker.invalid_y, (-1, 0))

    def test_update_boundaries(self):
        self.checker.update_boundaries((10, 20))
        self.assertEqual(self.checker.invalid_x, (0, 10))
        self.assertEqual(self.checker.invalid_y, (0, 20))

    def test_is_within_boundaries_valid(self):
        self.checker.update_boundaries((10, 20))
        self.assertTrue(self.checker.is_within_boundaries((5, 15)))

    def test_is_within_boundaries_invalid_x(self):
        self.checker.update_boundaries((10, 20))
        self.assertFalse(self.checker.is_within_boundaries((-2, 15)))
        self.assertFalse(self.checker.is_within_boundaries((12, 15)))

    def test_is_within_boundaries_invalid_y(self):
        self.checker.update_boundaries((10, 20))
        self.assertFalse(self.checker.is_within_boundaries((5, -2)))
        self.assertFalse(self.checker.is_within_boundaries((5, 22)))

    def test_repr(self):
        self.checker.update_boundaries((5, 7))
        self.assertEqual(
            repr(self.checker),
            "BoundaryChecker(invalid_x=(0, 5), invalid_y=(0, 7))",
        )

    def test_is_within_boundaries_on_edge_x_low(self):
        self.checker.update_boundaries((10, 20))
        self.assertTrue(self.checker.is_within_boundaries((0, 15)))

    def test_is_within_boundaries_on_edge_x_high(self):
        self.checker.update_boundaries((10, 20))
        self.assertFalse(self.checker.is_within_boundaries((10, 15)))

    def test_is_within_boundaries_on_edge_y_low(self):
        self.checker.update_boundaries((10, 20))
        self.assertTrue(self.checker.is_within_boundaries((5, 0)))

    def test_is_within_boundaries_on_edge_y_high(self):
        self.checker.update_boundaries((10, 20))
        self.assertFalse(self.checker.is_within_boundaries((5, 20)))

    def test_is_within_boundaries_zero_zero(self):
        self.checker.update_boundaries((10, 20))
        self.assertTrue(self.checker.is_within_boundaries((0, 0)))

    def test_get_boundary_validity_valid(self):
        self.checker.update_boundaries((10, 20))
        valid_x, valid_y = self.checker.get_boundary_validity((5, 15))
        self.assertTrue(valid_x)
        self.assertTrue(valid_y)

    def test_get_boundary_validity_invalid_x(self):
        self.checker.update_boundaries((10, 20))
        valid_x, valid_y = self.checker.get_boundary_validity((-2, 15))
        self.assertFalse(valid_x)
        self.assertTrue(valid_y)

    def test_get_boundary_validity_invalid_y(self):
        self.checker.update_boundaries((10, 20))
        valid_x, valid_y = self.checker.get_boundary_validity((5, -2))
        self.assertTrue(valid_x)
        self.assertFalse(valid_y)

    def test_set_area(self):
        self.checker.set_area((2, 3), (4, 5), (10, 20))
        self.assertEqual(self.checker.invalid_x, (2, 6))
        self.assertEqual(self.checker.invalid_y, (3, 8))

    def test_set_area_out_of_bounds_x(self):
        with self.assertRaises(ValueError):
            self.checker.set_area((11, 3), (4, 5), (10, 20))

    def test_set_area_out_of_bounds_y(self):
        with self.assertRaises(ValueError):
            self.checker.set_area((2, 21), (4, 5), (10, 20))

    def test_set_area_negative_size(self):
        with self.assertRaises(ValueError):
            self.checker.set_area((2, 3), (-4, 5), (10, 20))

    def test_set_area_zero_size(self):
        with self.assertRaises(ValueError):
            self.checker.set_area((2, 3), (0, 5), (10, 20))

    def test_set_area_from_center(self):
        self.checker.set_area_from_center((5, 10), 3, (10, 20))
        self.assertEqual(self.checker.invalid_x, (2, 8))
        self.assertEqual(self.checker.invalid_y, (7, 13))

    def test_set_area_from_center_out_of_bounds_x(self):
        self.checker.set_area_from_center((9, 10), 3, (10, 20))
        self.assertEqual(self.checker.invalid_x, (6, 10))

    def test_set_area_from_center_out_of_bounds_y(self):
        self.checker.set_area_from_center((5, 19), 3, (10, 20))
        self.assertEqual(self.checker.invalid_y, (16, 20))

    def test_set_area_from_center_negative_radius(self):
        with self.assertRaises(ValueError):
            self.checker.set_area_from_center((5, 10), -3, (10, 20))

    def test_reset_to_default(self):
        self.checker.update_boundaries((10, 20))
        self.checker.reset_to_default()
        self.assertEqual(self.checker.invalid_x, (-1, 0))
        self.assertEqual(self.checker.invalid_y, (-1, 0))
