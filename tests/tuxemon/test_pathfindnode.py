# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest

from tuxemon.movement import PathfindNode


class TestPathfindNode(unittest.TestCase):
    def test_initialization(self):
        node = PathfindNode((1, 2))
        self.assertEqual(node.get_value(), (1, 2))
        self.assertEqual(node.get_depth(), 0)

        parent = PathfindNode((0, 0))
        node = PathfindNode((1, 2), parent)
        self.assertEqual(node.get_value(), (1, 2))
        self.assertEqual(node.get_depth(), 1)

    def test_parent_and_depth(self):
        node = PathfindNode((1, 2))
        parent = PathfindNode((0, 0))
        node.set_parent(parent)
        self.assertEqual(node.get_parent(), parent)
        self.assertEqual(node.get_depth(), 1)

    def test_value(self):
        node = PathfindNode((3, 4))
        self.assertEqual(node.get_value(), (3, 4))

    def test_string_representation(self):
        node = PathfindNode((1, 2))
        self.assertEqual(str(node), "(1, 2)")

        parent = PathfindNode((0, 0))
        node.set_parent(parent)
        self.assertIn("(1, 2)", str(node))
        self.assertIn("(0, 0)", str(node))

    def test_edge_cases(self):
        node = PathfindNode(())
        self.assertEqual(node.get_value(), ())

        node = PathfindNode((1, 2), None)
        self.assertIsNone(node.get_parent())
        self.assertEqual(node.get_depth(), 0)

        with self.assertRaises(AttributeError):
            node = PathfindNode((1, 2), "invalid_parent")

    def test_large_values(self):
        value = (1000000, 1000000)
        node = PathfindNode(value)
        self.assertEqual(node.get_value(), value)

    def test_deep_hierarchy(self):
        parent = PathfindNode((0, 0))
        for _ in range(1000):
            parent = PathfindNode((1, 1), parent)
        self.assertEqual(parent.get_depth(), 1000)
