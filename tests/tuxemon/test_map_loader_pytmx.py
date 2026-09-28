# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from itertools import combinations
from operator import is_not
from unittest.mock import Mock

import pytest

from tuxemon.db import Direction
from tuxemon.map.loader import TMXMapLoader
from tuxemon.map.region import RegionProperties as RP


@pytest.fixture
def properties():
    return {
        "a": 1,
        "enter_from": Direction.UP,
        "b": 3,
        "exit_from": Direction.DOWN,
        "endure": Direction.LEFT,
    }


@pytest.fixture
def region(properties):
    return Mock(
        x=0,
        y=16,
        width=32,
        height=48,
        properties=properties,
    )


@pytest.fixture
def grid_size():
    return (16, 16)


@pytest.fixture
def result(region, grid_size):
    return list(TMXMapLoader.region_tiles(region, grid_size))


def test_result_is_point_and_properties_tuple(result):
    point, props = result[0]

    assert isinstance(point, tuple)
    assert len(point) == 2

    if props:
        assert isinstance(props, RP)


def test_result_properties_correct(result):
    _, props = result[0]

    expected = RP(
        enter_from=[Direction.UP],
        exit_from=[Direction.DOWN],
        endure=[Direction.LEFT],
        key=None,
    )

    if props:
        assert props == expected


def test_result_properties_is_not_same_object_as_input(result, properties):
    _, props = result[0]
    assert props is not properties


def test_result_each_properties_are_not_same_object(result):
    props_list = [p for _, p in result if p]
    for a, b in combinations(props_list, 2):
        assert is_not(a, b)


def test_correct_result(result):
    expected = [
        (
            (0, 1),
            RP([Direction.UP], [Direction.DOWN], [Direction.LEFT], None, None),
        ),
        (
            (1, 1),
            RP([Direction.UP], [Direction.DOWN], [Direction.LEFT], None, None),
        ),
        (
            (0, 2),
            RP([Direction.UP], [Direction.DOWN], [Direction.LEFT], None, None),
        ),
        (
            (1, 2),
            RP([Direction.UP], [Direction.DOWN], [Direction.LEFT], None, None),
        ),
        (
            (0, 3),
            RP([Direction.UP], [Direction.DOWN], [Direction.LEFT], None, None),
        ),
        (
            (1, 3),
            RP([Direction.UP], [Direction.DOWN], [Direction.LEFT], None, None),
        ),
    ]

    assert result == expected
