# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import pytest

from tuxemon.boundary import Dimensions, MapConditionBoundary
from tuxemon.db import BoundingBox


@pytest.fixture
def make_boundary():
    def _make(box: BoundingBox):
        return MapConditionBoundary(box)

    return _make


def test_tile_inside_condition(make_boundary):
    boundary = make_boundary(BoundingBox(x=0, y=0, width=5, height=5))
    assert boundary.is_within((2, 2))


def test_tile_outside_condition(make_boundary):
    boundary = make_boundary(BoundingBox(x=0, y=0, width=5, height=5))
    assert not boundary.is_within((6, 6))


def test_tile_on_edge_condition(make_boundary):
    boundary = make_boundary(BoundingBox(x=0, y=0, width=5, height=5))
    assert boundary.is_within((0, 0))
    assert boundary.is_within((4, 4))


def test_invalid_tile_position(make_boundary):
    boundary = make_boundary(BoundingBox(x=0, y=0, width=5, height=5))
    with pytest.raises(TypeError):
        boundary.is_within("invalid")


def test_edge_cases_for_condition_dimensions(make_boundary):
    boundary = make_boundary(BoundingBox(x=0, y=0, width=1, height=1))
    assert not boundary.is_within((1, 1))

    boundary = make_boundary(BoundingBox(x=0, y=0, width=1, height=1))
    assert boundary.is_within((0, 0))


def test_negative_coordinates(make_boundary):
    boundary = make_boundary(BoundingBox(x=-2, y=-2, width=5, height=5))
    assert boundary.is_within((0, 0))


def test_large_coordinates(make_boundary):
    boundary = make_boundary(BoundingBox(x=10000, y=10000, width=5, height=5))
    assert boundary.is_within((10001, 10001))


def test_edge_cases_zero_width_or_height(make_boundary):
    boundary = make_boundary(BoundingBox(x=0, y=0, width=1, height=5))
    assert not boundary.is_within((1, 1))

    boundary = make_boundary(BoundingBox(x=0, y=0, width=5, height=1))
    assert not boundary.is_within((1, 1))


def test_move_shifts_boundary_position(make_boundary):
    boundary = make_boundary(BoundingBox(x=0, y=0, width=5, height=5))
    assert boundary.is_within((2, 2))

    boundary.move(3, 3)
    assert not boundary.is_within((2, 2))
    assert boundary.is_within((5, 5))
    assert boundary.get_center() == (5.5, 5.5)


def test_resize_expands_boundary(make_boundary):
    boundary = make_boundary(BoundingBox(x=0, y=0, width=2, height=2))
    assert not boundary.is_within((3, 3))

    boundary.resize(2, 2)
    assert boundary.is_within((3, 3))
    assert boundary.get_dimensions() == Dimensions(width=4.0, height=4.0)


def test_resize_contracts_boundary(make_boundary):
    boundary = make_boundary(BoundingBox(x=0, y=0, width=5, height=5))
    assert boundary.is_within((4, 4))

    boundary.resize(-3, -3)
    assert not boundary.is_within((4, 4))
    assert boundary.get_dimensions() == Dimensions(width=2.0, height=2.0)


def test_resize_to_zero_dimensions(make_boundary):
    boundary = make_boundary(BoundingBox(x=0, y=0, width=2, height=2))
    boundary.resize(-2, -2)
    assert not boundary.is_within((0, 0))
    assert boundary.get_dimensions() == Dimensions(width=0.0, height=0.0)


def test_move_and_resize_combination(make_boundary):
    boundary = make_boundary(BoundingBox(x=0, y=0, width=3, height=3))
    boundary.move(2, 2)
    boundary.resize(2, 2)

    assert boundary.is_within((4, 4))
    assert not boundary.is_within((1, 1))
    assert boundary.get_center() == (4.5, 4.5)
