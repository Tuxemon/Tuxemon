# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from collections.abc import Mapping
from typing import Any

import pytest

from tuxemon.tracker import (
    TrackingData,
    TrackingPoint,
    decode_tracking,
    encode_tracking,
)


def test_tracking_point_get_state():
    point = TrackingPoint(visited=False)
    assert point.get_state() == {"visited": False}


@pytest.fixture
def tracking_data():
    return TrackingData()


@pytest.fixture
def point():
    return TrackingPoint()


def test_add_location(tracking_data, point):
    tracking_data.add_location("loc_1", point)
    assert "loc_1" in tracking_data.locations
    assert tracking_data.locations["loc_1"] is point


def test_add_duplicate_location(tracking_data, point):
    tracking_data.add_location("loc_1", point)
    tracking_data.add_location("loc_1", point)
    assert len(tracking_data.locations) == 1


def test_remove_location(tracking_data, point):
    tracking_data.add_location("loc_1", point)
    tracking_data.remove_location("loc_1")
    assert "loc_1" not in tracking_data.locations


def test_remove_non_existent_location(tracking_data):
    initial = len(tracking_data.locations)
    tracking_data.remove_location("loc_999")
    assert len(tracking_data.locations) == initial


def test_get_location(tracking_data, point):
    tracking_data.add_location("loc_1", point)
    assert tracking_data.get_location("loc_1") is point


def test_get_non_existent_location(tracking_data):
    assert tracking_data.get_location("loc_999") is None


def test_encode_tracking():
    data = TrackingData()
    data.add_location("loc_1", TrackingPoint(visited=True))
    data.add_location("loc_2", TrackingPoint(visited=False))

    encoded = encode_tracking(data)

    expected = {
        "loc_1": {"visited": True},
        "loc_2": {"visited": False},
    }

    assert encoded == expected


def test_decode_tracking():
    json_data: Mapping[str, Any] = {
        "loc_1": {"visited": True},
        "loc_2": {"visited": False},
    }

    data = decode_tracking(json_data)

    assert "loc_1" in data.locations
    assert "loc_2" in data.locations
    assert data.get_location("loc_1").visited is True
    assert data.get_location("loc_2").visited is False
