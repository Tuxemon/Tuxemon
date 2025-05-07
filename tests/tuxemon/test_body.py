# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest

from tuxemon.entity import Body
from tuxemon.math import Point3, Vector3


class TestBody(unittest.TestCase):
    def setUp(self):
        self.body = Body(position=Point3(0, 0, 0))

    def test_initialization(self):
        self.assertEqual(self.body.position, Point3(0, 0, 0))
        self.assertEqual(self.body.velocity, Vector3(0, 0, 0))
        self.assertEqual(self.body.acceleration, Vector3(0, 0, 0))

    def test_update_position(self):
        self.body.velocity = Vector3(1, 1, 0)
        self.body.acceleration = Vector3(1, 0, 0)
        self.body.update(time_delta=1.0)

        self.assertEqual(self.body.position, Point3(2, 1, 0))
        self.assertEqual(self.body.velocity, Vector3(2, 1, 0))

    def test_stop(self):
        self.body.velocity = Vector3(5, 5, 5)
        self.body.stop()

        self.assertEqual(self.body.velocity, Vector3(0, 0, 0))

    def test_reset(self):
        self.body.position = Point3(10, 10, 10)
        self.body.velocity = Vector3(5, 5, 5)
        self.body.acceleration = Vector3(1, 1, 1)
        self.body.reset()

        self.assertEqual(self.body.position, Point3(0, 0, 0))
        self.assertEqual(self.body.velocity, Vector3(0, 0, 0))
        self.assertEqual(self.body.acceleration, Vector3(0, 0, 0))
