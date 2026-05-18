# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import pytest

from tuxemon.db import BoundingBox, EventObject
from tuxemon.map.loader import EventParser


@pytest.fixture
def parser():
    return EventParser()


@pytest.fixture
def box():
    return BoundingBox(x=5, y=10, width=2, height=3)


@pytest.fixture
def base_event_data():
    return {
        "behav": ["walk:north"],
        "conditions": ["is flag quest_started"],
        "actions": ["set flag quest_completed"],
    }


def test_create_event_object(parser, base_event_data, box):
    event = parser.create_event_object(base_event_data, "test_event", box)
    assert isinstance(event, EventObject)
    assert event.name == "test_event"
    assert event.box.x == box.x
    assert len(event.behavs) == 1
    beh = event.behavs[0]
    assert beh.type == "walk:north"
    assert beh.args == []
    assert len(event.conds) == 1
    cond = event.conds[0]
    assert cond.type == "flag"
    assert cond.parameters == ["quest_started"]
    assert cond.operator == "is"
    assert len(event.acts) == 1
    act = event.acts[0]
    assert act.type == "set"
    assert act.parameters == ["flag quest_completed"]


def test_empty_event_data(parser, box):
    event = parser.create_event_object({}, "empty", box)
    assert event.conds == []
    assert event.acts == []
    assert event.behavs == []


def test_behav_only(parser, box):
    data = {"behav": ["run:east"]}
    event = parser.create_event_object(data, "behav_only", box)
    assert len(event.behavs) == 1
    beh = event.behavs[0]
    assert beh.type == "run:east"
    assert beh.args == []
    assert event.conds == []
    assert event.acts == []


def test_malformed_condition(parser, box):
    data = {"conditions": ["is"]}
    with pytest.raises(ValueError):
        parser.create_event_object(data, "bad", box)


@pytest.mark.parametrize(
    "behav_list, expected_names",
    [
        pytest.param(
            ["jump:up", "slide:left"],
            ["behav10", "behav20"],
            id="two_behaviors_jump_slide",
        ),
        pytest.param(
            ["a:1", "b:2", "c:3"],
            ["behav10", "behav20", "behav30"],
            id="three_behaviors_abc",
        ),
    ],
)
def test_multiple_behaviors(parser, box, behav_list, expected_names):
    data = {"behav": behav_list}
    event = parser.create_event_object(data, "multi", box)
    assert len(event.behavs) == len(behav_list)
    assert [b.name for b in event.behavs] == expected_names


def test_complex_action(parser, box):
    data = {"actions": ["set flag quest_completed:true"]}
    event = parser.create_event_object(data, "complex", box)
    assert event.acts[0].parameters == ["flag quest_completed:true"]


def test_event_object_integrity(parser, base_event_data, box):
    event = parser.create_event_object(base_event_data, "test_event", box)
    assert hasattr(event, "id")
    assert event.name == "test_event"
    assert event.box.x == box.x
    assert event.box.y == box.y


def test_event_with_timeout_and_delay(parser, box):
    event = parser.create_event_object(
        {"timeout": 5, "delay": 2},
        "timed",
        box,
        timeout=5.0,
        delay=2.0,
    )
    assert event.timeout == 5.0
    assert event.delay == 2.0


def test_event_defaults(parser, box):
    event = parser.create_event_object({}, "default", box)
    assert event.timeout is None
    assert event.delay is None


def test_condition_with_not_operator(parser, box):
    data = {"conditions": ["not flag quest_started"]}
    event = parser.create_event_object(data, "not_cond", box)
    cond = event.conds[0]
    assert cond.operator == "not"


def test_event_box_integrity(parser, base_event_data, box):
    event = parser.create_event_object(base_event_data, "box_test", box)
    assert event.box.width == 2
    assert event.box.height == 3


def test_multiple_actions(parser, box):
    data = {
        "actions": [
            "set flag quest_started",
            "clear flag quest_completed",
        ]
    }
    event = parser.create_event_object(data, "multi_actions", box)
    assert len(event.acts) == 2
    assert event.acts[0].type == "set"
    assert event.acts[1].type == "clear"
