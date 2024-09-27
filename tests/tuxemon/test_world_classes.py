# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest

from tuxemon.states.world.world_classes import BoundaryChecker


class TestBoundaryChecker(unittest.TestCase):
    def setUp(self):
        self.checker = BoundaryChecker()

    def test_initial_boundaries(self):
        self.assertEqual(self.checker.invalid_x, (-1, 0))
        self.assertEqual(self.checker.invalid_y, (-1, 0))

    def test_update_boundaries(self):
        self.checker.update_boundaries((10, 20))
        self.assertEqual(self.checker.invalid_x, (-1, 10))
        self.assertEqual(self.checker.invalid_y, (-1, 20))

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
            "BoundaryChecker(invalid_x=(-1, 5), invalid_y=(-1, 7))",
        )
