# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from pathlib import Path

import pytest

from tuxemon.database.yaml_utils import load_yaml
from tuxemon.map.loader import YAMLEventLoader


@pytest.fixture
def yaml_path():
    return Path("tests/tuxemon") / "test_event_loader_map.yaml"


@pytest.fixture
def loader():
    return YAMLEventLoader()


def test_parse_yaml_success(yaml_path):
    result = load_yaml(yaml_path)
    assert isinstance(result, dict)
    assert "events" in result
    assert isinstance(result["events"], dict)
    assert "test_event" in result["events"]


def test_load_events(loader, yaml_path):
    result = loader.load_events(yaml_path, "event")
    assert "event" in result
    events = result["event"]
    assert isinstance(events, list)
    assert events, "Expected at least one event"
    event = events[0]
    assert event.name == "test_event"
    assert event.box.x == 1
    assert event.box.y == 2
    assert event.box.width == 3
    assert event.box.height == 4
    assert hasattr(event, "acts")
    assert hasattr(event, "conds")
    assert hasattr(event, "behavs")
    assert len(event.acts) > 0
    assert len(event.conds) > 0
    assert len(event.behavs) > 0


def test_load_collision(loader, yaml_path):
    result = loader.load_collision(yaml_path)
    expected_tiles = {(2, 4), (3, 4), (2, 5), (3, 5)}

    for tile in expected_tiles:
        assert tile in result

    assert result[(2, 4)] is None
