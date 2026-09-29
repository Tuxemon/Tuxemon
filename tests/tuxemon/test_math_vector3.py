# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import pytest

from tuxemon.math import Vector3


def test_initialization():
    assert tuple(Vector3()) == (0, 0, 0)
    assert tuple(Vector3(1, 2, 3)) == (1, 2, 3)
    assert tuple(Vector3([4, 5, 6])) == (4, 5, 6)


def test_addition():
    v1 = Vector3(1, 2, 3)
    v2 = Vector3(4, 5, 6)
    assert tuple(v1 + v2) == (5, 7, 9)


@pytest.mark.parametrize(
    "vector, scalar, expected",
    [
        pytest.param(Vector3(1, 2, 3), 2, (2, 4, 6), id="scalar_positive"),
        pytest.param(Vector3(1, 2, 3), -1, (-1, -2, -3), id="scalar_negative"),
        pytest.param(Vector3(3, -3, 6), 0, (0, 0, 0), id="scalar_zero"),
    ],
)
def test_scalar_multiplication(vector, scalar, expected):
    assert tuple(vector * scalar) == expected
    assert tuple(scalar * vector) == expected


def test_iteration():
    assert list(Vector3(1, 2, 3)) == [1, 2, 3]


def test_equality():
    assert Vector3(1, 2, 3) == Vector3(1, 2, 3)
    assert Vector3(1, 2, 3) != Vector3(4, 5, 6)


def test_getitem():
    v = Vector3(1, 2, 3)
    assert v[0] == 1
    assert v[1] == 2
    assert v[2] == 3
    assert v[0:2] == (1, 2)


@pytest.mark.parametrize(
    "vector, expected",
    [
        pytest.param(Vector3(1, 2, 2), 3.0, id="magnitude_1_2_2"),
        pytest.param(Vector3(0, 0, 0), 0.0, id="magnitude_zero"),
        pytest.param(
            Vector3(10, 10, 10),
            pytest.approx(17.32, abs=0.01),
            id="magnitude_large",
        ),
    ],
)
def test_vector3_magnitude(vector, expected):
    assert pytest.approx(vector.magnitude, abs=0.01) == expected


def test_vector3_normalized():
    v = Vector3(1, 2, 2)
    n = v.normalized

    assert pytest.approx(n.magnitude, abs=0.01) == 1.0
    assert pytest.approx(n[0], abs=0.01) == 0.33
    assert pytest.approx(n[1], abs=0.01) == 0.67
    assert pytest.approx(n[2], abs=0.01) == 0.67

    zero = Vector3(0, 0, 0).normalized
    assert zero.magnitude == 0.0


def test_scalar_division():
    v = Vector3(9, 18, 27)
    assert tuple(v / 3) == (3.0, 6.0, 9.0)


def test_vector_subtraction():
    v1 = Vector3(10, 20, 30)
    v2 = Vector3(1, 2, 3)

    assert tuple(v1 - v2) == (9, 18, 27)
    assert tuple(v1 - (5, 5, 5)) == (5, 15, 25)


def test_reverse_subtraction():
    v1 = Vector3(2, 4, 6)

    assert tuple((10, 10, 10) - v1) == (8, 6, 4)
    assert tuple(Vector3(5, 5, 5) - Vector3(1, 2, 3)) == (4, 3, 2)
