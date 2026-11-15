# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import pytest

from tuxemon.math import Vector2


def test_initialization():
    assert tuple(Vector2()) == (0, 0)
    assert tuple(Vector2(1, 2)) == (1, 2)
    assert tuple(Vector2([4, 5])) == (4, 5)


def test_addition():
    v1 = Vector2(1, 2)
    v2 = Vector2(3, 4)
    assert tuple(v1 + v2) == (4, 6)


@pytest.mark.parametrize(
    "vector, scalar, expected",
    [
        pytest.param(Vector2(1, 2), 2, (2, 4), id="positive_scalar"),
        pytest.param(Vector2(1, 2), -1, (-1, -2), id="negative_scalar"),
        pytest.param(Vector2(3, -3), 0, (0, 0), id="zero_scalar"),
    ],
)
def test_scalar_multiplication(vector, scalar, expected):
    assert tuple(vector * scalar) == expected
    assert tuple(scalar * vector) == expected


def test_iteration():
    v = Vector2(1, 2)
    assert list(v) == [1, 2]


def test_equality():
    assert Vector2(1, 2) == Vector2(1, 2)
    assert Vector2(1, 2) != Vector2(3, 4)


def test_getitem():
    v = Vector2(1, 2)
    assert v[0] == 1
    assert v[1] == 2
    assert v[0:2] == (1, 2)


@pytest.mark.parametrize(
    "vector, expected",
    [
        pytest.param(Vector2(3, 4), 5.0, id="magnitude_3_4"),
        pytest.param(Vector2(0, 0), 0.0, id="magnitude_zero"),
        pytest.param(
            Vector2(1, 1), pytest.approx(1.41, abs=0.01), id="magnitude_diag"
        ),
    ],
)
def test_vector2_magnitude(vector, expected):
    assert pytest.approx(vector.magnitude, abs=0.01) == expected


def test_vector2_normalized():
    v = Vector2(3, 4)
    n = v.normalized

    assert pytest.approx(n.magnitude, abs=0.01) == 1.0
    assert pytest.approx(n[0], abs=0.01) == 0.6
    assert pytest.approx(n[1], abs=0.01) == 0.8

    zero = Vector2(0, 0).normalized
    assert zero.magnitude == 0.0


def test_scalar_division():
    v = Vector2(10, 20)
    assert tuple(v / 2) == (5.0, 10.0)


def test_vector_subtraction():
    v1 = Vector2(5, 7)
    v2 = Vector2(2, 3)

    assert tuple(v1 - v2) == (3, 4)
    assert tuple(v1 - (1, 2)) == (4, 5)


def test_reverse_subtraction():
    v1 = Vector2(2, 3)

    assert tuple((5, 7) - v1) == (3, 4)
    assert tuple(Vector2(10, 10) - Vector2(5, 3)) == (5, 7)
