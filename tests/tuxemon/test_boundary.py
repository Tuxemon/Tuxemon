# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import pytest

from tuxemon.boundary import (
    BoundaryChecker,
    CircularBoundary,
    CompositeBoundary,
    InvertedBoundary,
    NullBoundary,
    RectangularBoundary,
    TaggedBoundary,
)


@pytest.fixture
def checker():
    return BoundaryChecker()


# BoundaryChecker tests


@pytest.mark.parametrize(
    "point",
    [
        pytest.param((0, 0), id="origin"),
        pytest.param((-1, -1), id="negative_coords"),
        pytest.param((999, 999), id="large_coords"),
    ],
)
def test_default_boundary_rejects_all(checker, point):
    assert not checker.is_within_boundaries(point)


def test_set_rectangular_boundary(checker):
    checker.set_rectangular_boundary("map", 2, 6, 3, 8)

    assert checker.is_within_boundaries((3, 4))
    assert not checker.is_within_boundaries((1, 4))
    assert not checker.is_within_boundaries((6, 4))
    assert not checker.is_within_boundaries((3, 8))


@pytest.mark.parametrize(
    "point, expected_x, expected_y",
    [
        pytest.param((3, 4), True, True, id="point_inside"),
        pytest.param((6, 4), False, True, id="point_x_outside"),
    ],
)
def test_get_boundary_validity_rectangular(
    checker, point, expected_x, expected_y
):
    checker.set_rectangular_boundary("map", 0, 5, 0, 5)
    valid_x, valid_y = checker.get_boundary_validity(point)
    assert valid_x is expected_x
    assert valid_y is expected_y


def test_get_boundary_validity_raises_on_non_rectangular(checker):
    checker.set_circular_boundary("map", (5, 5), 3)
    with pytest.raises(TypeError):
        checker.get_boundary_validity((5, 5))


@pytest.mark.parametrize(
    "point, expected",
    [
        pytest.param((10, 10), True, id="center"),
        pytest.param((13, 13), True, id="inside"),
        pytest.param((16, 10), False, id="outside_x"),
        pytest.param((10, 16), False, id="outside_y"),
    ],
)
def test_set_circular_boundary(checker, point, expected):
    checker.set_circular_boundary("map", (10, 10), 5)
    assert checker.is_within_boundaries(point) is expected


def test_reset_to_default(checker):
    checker.set_rectangular_boundary("map", 0, 10, 0, 10)
    assert checker.is_within_boundaries((5, 5))
    checker.reset_to_default()
    assert not checker.is_within_boundaries((5, 5))


def test_repr_contains_boundary_type(checker):
    checker.set_rectangular_boundary("map", 0, 5, 0, 5)
    assert "RectangularBoundary" in repr(checker)

    checker.set_circular_boundary("map", (5, 5), 2)
    assert "CircularBoundary" in repr(checker)


def test_repr_shows_reject_all_boundary(checker):
    checker.reset_to_default()
    assert "NullBoundary" in repr(checker)


@pytest.mark.parametrize(
    "point, expected",
    [
        pytest.param((0, 0), True, id="bottom_left"),
        pytest.param((9, 0), True, id="bottom_right_inside"),
        pytest.param((0, 9), True, id="top_left_inside"),
        pytest.param((9, 9), True, id="top_right_inside"),
        pytest.param((10, 5), False, id="right_edge_outside"),
        pytest.param((5, 10), False, id="top_edge_outside"),
        pytest.param((10, 10), False, id="corner_outside"),
    ],
)
def test_rectangular_boundary_edges(checker, point, expected):
    checker.set_rectangular_boundary("map", 0, 10, 0, 10)
    assert checker.is_within_boundaries(point) is expected


# CompositeBoundary tests


def test_union_combines_multiple_boundaries():
    rect = RectangularBoundary((0, 5), (0, 5))
    circle = CircularBoundary((10, 10), 3)
    combo = CompositeBoundary([rect, circle], mode="union")

    assert combo.is_within((2, 2))
    assert combo.is_within((10, 10))
    assert not combo.is_within((7, 7))


def test_intersection_requires_all_boundaries():
    rect = RectangularBoundary((0, 10), (0, 10))
    circle = CircularBoundary((5, 5), 3)
    combo = CompositeBoundary([rect, circle], mode="intersection")

    assert combo.is_within((5, 5))
    assert not combo.is_within((9, 9))
    assert not combo.is_within((2, 2))


@pytest.mark.parametrize(
    "mode, expected",
    [
        pytest.param("union", False, id="union_empty_false"),
        pytest.param("intersection", True, id="intersection_empty_true"),
    ],
)
def test_empty_composite(mode, expected):
    combo = CompositeBoundary([], mode=mode)
    assert combo.is_within((0, 0)) is expected


def test_invalid_mode_raises():
    with pytest.raises(ValueError):
        CompositeBoundary([], mode="invalid")


# Movement tests


def test_move_rectangular_boundary():
    boundary = RectangularBoundary((0, 5), (0, 5))
    assert boundary.is_within((2, 2))

    boundary.move(3, 3)
    assert not boundary.is_within((2, 2))
    assert boundary.is_within((5, 5))
    assert boundary.get_center() == (5.5, 5.5)


def test_move_circular_boundary():
    boundary = CircularBoundary((5, 5), 3)
    assert boundary.is_within((5, 5))

    boundary.move(2, -1)
    assert not boundary.is_within((3, 3))
    assert boundary.is_within((7, 4))


def test_move_null_boundary():
    boundary = NullBoundary()
    boundary.move(100, 100)
    assert not boundary.is_within((0, 0))
    assert boundary.get_center() == (0.0, 0.0)


def test_move_inverted_boundary():
    base = RectangularBoundary((0, 5), (0, 5))
    boundary = InvertedBoundary(base)

    assert not boundary.is_within((2, 2))
    boundary.move(5, 5)
    assert boundary.is_within((2, 2))


def test_move_tagged_boundary():
    base = CircularBoundary((10, 10), 2)
    boundary = TaggedBoundary(base, "safe_zone")

    assert boundary.is_within((10, 10))
    boundary.move(-5, -5)
    assert not boundary.is_within((10, 10))
    assert boundary.is_within((5, 5))


def test_move_composite_boundary():
    b1 = RectangularBoundary((0, 5), (0, 5))
    b2 = CircularBoundary((10, 10), 3)
    composite = CompositeBoundary([b1, b2], mode="union")

    assert composite.is_within((2, 2))
    assert composite.is_within((10, 10))

    composite.move(5, 5)
    assert not composite.is_within((2, 2))
    assert composite.is_within((7, 7))
    assert composite.is_within((15, 15))
