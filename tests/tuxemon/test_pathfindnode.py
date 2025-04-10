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

    def test_circular_reference(self):
        node = PathfindNode((1, 2))
        with self.assertRaises(ValueError):
            node.set_parent(node)

    def test_reconstruct_path(self):
        root = PathfindNode((0, 0))
        child = PathfindNode((1, 1), root)
        grandchild = PathfindNode((2, 2), child)

        self.assertEqual(grandchild.reconstruct_path(), [(2, 2), (1, 1)])

    def test_reconstruct_path_single_node(self):
        node = PathfindNode((0, 0))
        self.assertEqual(node.reconstruct_path(), [])

    def test_invalid_parent_assignment(self):
        node = PathfindNode((1, 2))
        with self.assertRaises(ValueError):
            node.set_parent(None)
        # Parent cannot be the node itself
        with self.assertRaises(ValueError):
            node.set_parent(node)

    def test_boundary_values(self):
        # Max value for a 32-bit integer
        max_int = (2147483647, 2147483647)
        node = PathfindNode(max_int)
        self.assertEqual(node.get_value(), max_int)
        # Min value for a 32-bit integer
        min_int = (-2147483648, -2147483648)
        node = PathfindNode(min_int)
        self.assertEqual(node.get_value(), min_int)

    def test_depth_update(self):
        root = PathfindNode((0, 0))
        child = PathfindNode((1, 1), root)
        self.assertEqual(child.get_depth(), 1)

        grandchild = PathfindNode((2, 2), child)
        self.assertEqual(grandchild.get_depth(), 2)

        grandchild.set_parent(root)
        self.assertEqual(grandchild.get_depth(), 1)

    def test_multi_level_string_representation(self):
        parent = PathfindNode((0, 0))
        child = PathfindNode((1, 1), parent)
        grandchild = PathfindNode((2, 2), child)

        self.assertIn("(0, 0)", str(grandchild))
        self.assertIn("(1, 1)", str(grandchild))
        self.assertIn("(2, 2)", str(grandchild))

    def test_large_hierarchy_performance(self):
        root = PathfindNode((0, 0))
        current = root
        # Create a deep hierarchy
        for i in range(10000):
            current = PathfindNode((i + 1, i + 1), current)
        self.assertEqual(len(current.reconstruct_path()), 10000)
