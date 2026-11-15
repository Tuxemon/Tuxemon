# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import pytest

from tuxemon.movement import PathfindNode


@pytest.fixture
def root_node():
    return PathfindNode((0, 0))


@pytest.fixture
def child_node(root_node):
    return PathfindNode((1, 1), root_node)


@pytest.fixture
def grandchild_node(child_node):
    return PathfindNode((2, 2), child_node)


@pytest.mark.parametrize(
    "value, parent, expected_depth",
    [
        pytest.param((1, 2), None, 0, id="no_parent_depth0"),
        pytest.param((1, 2), PathfindNode((0, 0)), 1, id="with_parent_depth1"),
        pytest.param((3, 4), None, 0, id="simple_no_parent"),
        pytest.param((2147483647, 2147483647), None, 0, id="max_int_values"),
        pytest.param((-2147483648, -2147483648), None, 0, id="min_int_values"),
    ],
)
def test_initialization_and_values(value, parent, expected_depth):
    node = PathfindNode(value, parent)
    assert node.get_value() == value
    assert node.get_depth() == expected_depth


@pytest.mark.parametrize(
    "value",
    [
        pytest.param((), id="empty_tuple"),
        pytest.param((1000000, 1000000), id="large_values"),
    ],
)
def test_edge_and_large_values(value):
    node = PathfindNode(value)
    assert node.get_value() == value


def test_parent_and_depth(root_node):
    node = PathfindNode((1, 2))
    node.set_parent(root_node)
    assert node.get_parent() == root_node
    assert node.get_depth() == 1


@pytest.mark.parametrize(
    "value, expected_str",
    [
        pytest.param((1, 2), "(1, 2)", id="simple_1_2"),
        pytest.param((0, 0), "(0, 0)", id="simple_0_0"),
    ],
)
def test_string_representation_simple(value, expected_str):
    node = PathfindNode(value)
    assert expected_str in str(node)


def test_string_representation_multi_level(grandchild_node):
    s = str(grandchild_node)
    assert "(0, 0)" in s
    assert "(1, 1)" in s
    assert "(2, 2)" in s


@pytest.mark.parametrize(
    "invalid_parent, expected_exception",
    [
        pytest.param("invalid_parent", AttributeError, id="non_node_parent"),
        pytest.param(None, ValueError, id="none_parent"),
    ],
)
def test_invalid_parent_assignment(invalid_parent, expected_exception):
    node = PathfindNode((1, 2))
    with pytest.raises(expected_exception):
        node.set_parent(invalid_parent)


def test_circular_reference():
    node = PathfindNode((1, 2))
    with pytest.raises(ValueError):
        node.set_parent(node)


def test_deep_hierarchy(root_node):
    parent = root_node
    for _ in range(1000):
        parent = PathfindNode((1, 1), parent)
    assert parent.get_depth() == 1000


def test_large_hierarchy_performance(root_node):
    current = root_node
    for i in range(10000):
        current = PathfindNode((i + 1, i + 1), current)
    assert len(current.reconstruct_path()) == 10000


def test_reconstruct_path(grandchild_node):
    assert grandchild_node.reconstruct_path() == [(2, 2), (1, 1)]


def test_reconstruct_path_single_node(root_node):
    assert root_node.reconstruct_path() == []


def test_reconstruct_path_after_parent_change(child_node):
    alt_root = PathfindNode((9, 9))
    child_node.set_parent(alt_root)
    assert child_node.reconstruct_path() == [(1, 1)]


def test_branching_path_reconstruction(root_node):
    PathfindNode((1, 0), root_node)
    branch2 = PathfindNode((0, 1), root_node)
    leaf = PathfindNode((1, 1), branch2)
    assert leaf.reconstruct_path() == [(1, 1), (0, 1)]


@pytest.mark.parametrize(
    "g_cost, h_cost, other_g, other_h, expected",
    [
        pytest.param(1.0, 2.0, 2.0, 2.0, True, id="3_lt_4"),
        pytest.param(2.0, 2.0, 1.0, 2.0, False, id="4_gt_3"),
    ],
)
def test_node_comparison_by_f_cost(g_cost, h_cost, other_g, other_h, expected):
    node1 = PathfindNode((0, 0), g_cost=g_cost, h_cost=h_cost)
    node2 = PathfindNode((1, 1), g_cost=other_g, h_cost=other_h)
    assert (node1 < node2) == expected


def test_node_equality():
    node1 = PathfindNode((1, 2))
    node2 = PathfindNode((1, 2))
    assert node1 != node2


def test_depth_update(root_node, child_node):
    assert child_node.get_depth() == 1

    grandchild = PathfindNode((2, 2), child_node)
    assert grandchild.get_depth() == 2

    grandchild.set_parent(root_node)
    assert grandchild.get_depth() == 1
