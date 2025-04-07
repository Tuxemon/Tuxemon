# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest

from tuxemon.math import Vector2, Vector3


class TestVector3(unittest.TestCase):
    def test_initialization(self):
        v1 = Vector3()
        self.assertEqual(tuple(v1), (0, 0, 0))

        v2 = Vector3(1, 2, 3)
        self.assertEqual(tuple(v2), (1, 2, 3))

        v3 = Vector3([4, 5, 6])
        self.assertEqual(tuple(v3), (4, 5, 6))

    def test_addition(self):
        v1 = Vector3(1, 2, 3)
        v2 = Vector3(4, 5, 6)
        result = v1 + v2
        self.assertEqual(tuple(result), (5, 7, 9))

    def test_scalar_multiplication(self):
        v1 = Vector3(1, 2, 3)
        result = v1 * 2
        self.assertEqual(tuple(result), (2, 4, 6))

        result = 2 * v1
        self.assertEqual(tuple(result), (2, 4, 6))

    def test_iteration(self):
        v1 = Vector3(1, 2, 3)
        values = list(iter(v1))
        self.assertEqual(values, [1, 2, 3])

    def test_equality(self):
        v1 = Vector3(1, 2, 3)
        v2 = Vector3(1, 2, 3)
        v3 = Vector3(4, 5, 6)
        self.assertTrue(v1 == v2)
        self.assertFalse(v1 == v3)

    def test_getitem(self):
        v1 = Vector3(1, 2, 3)
        self.assertEqual(v1[0], 1)
        self.assertEqual(v1[1], 2)
        self.assertEqual(v1[2], 3)
        self.assertEqual(v1[0:2], (1, 2))

    def test_vector3_magnitude(self):
        v3 = Vector3(1, 2, 2)
        self.assertAlmostEqual(v3.magnitude, 3.0, places=2)

        v3_zero = Vector3(0, 0, 0)
        self.assertAlmostEqual(v3_zero.magnitude, 0.0, places=2)

        v3_large = Vector3(10, 10, 10)
        self.assertAlmostEqual(v3_large.magnitude, 17.32, places=2)

    def test_vector3_normalized(self):
        v3 = Vector3(1, 2, 2)
        normalized_v3 = v3.normalized
        self.assertAlmostEqual(normalized_v3.magnitude, 1.0, places=2)
        self.assertAlmostEqual(normalized_v3[0], 0.33, places=2)
        self.assertAlmostEqual(normalized_v3[1], 0.67, places=2)
        self.assertAlmostEqual(normalized_v3[2], 0.67, places=2)

        v3_zero = Vector3(0, 0, 0)
        normalized_v3_zero = v3_zero.normalized
        self.assertEqual(normalized_v3_zero.magnitude, 0.0)


class TestVector2(unittest.TestCase):
    def test_initialization(self):
        v1 = Vector2()
        self.assertEqual(tuple(v1), (0, 0))

        v2 = Vector2(1, 2)
        self.assertEqual(tuple(v2), (1, 2))

        v3 = Vector2([4, 5])
        self.assertEqual(tuple(v3), (4, 5))

    def test_addition(self):
        v1 = Vector2(1, 2)
        v2 = Vector2(3, 4)
        result = v1 + v2
        self.assertEqual(tuple(result), (4, 6))

    def test_scalar_multiplication(self):
        v1 = Vector2(1, 2)
        result = v1 * 2
        self.assertEqual(tuple(result), (2, 4))

        result = 2 * v1
        self.assertEqual(tuple(result), (2, 4))

    def test_iteration(self):
        v1 = Vector2(1, 2)
        values = list(iter(v1))
        self.assertEqual(values, [1, 2])

    def test_equality(self):
        v1 = Vector2(1, 2)
        v2 = Vector2(1, 2)
        v3 = Vector2(3, 4)
        self.assertTrue(v1 == v2)
        self.assertFalse(v1 == v3)

    def test_getitem(self):
        v1 = Vector2(1, 2)
        self.assertEqual(v1[0], 1)
        self.assertEqual(v1[1], 2)
        self.assertEqual(v1[0:2], (1, 2))

    def test_vector2_magnitude(self):
        v2 = Vector2(3, 4)
        self.assertAlmostEqual(v2.magnitude, 5.0, places=2)

        v2_zero = Vector2(0, 0)
        self.assertAlmostEqual(v2_zero.magnitude, 0.0, places=2)

        v2_diagonal = Vector2(1, 1)
        self.assertAlmostEqual(v2_diagonal.magnitude, 1.41, places=2)

    def test_vector2_normalized(self):
        v2 = Vector2(3, 4)
        normalized_v2 = v2.normalized
        self.assertAlmostEqual(normalized_v2.magnitude, 1.0, places=2)
        self.assertAlmostEqual(normalized_v2[0], 0.6, places=2)
        self.assertAlmostEqual(normalized_v2[1], 0.8, places=2)

        v2_zero = Vector2(0, 0)
        normalized_v2_zero = v2_zero.normalized
        self.assertEqual(normalized_v2_zero.magnitude, 0.0)
