# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from typing import Any

import pytest

from tuxemon.state.builder import StateBuilder


class MockState:
    def __init__(self, name: str, level: int, metadata: dict[str, Any] = None):
        self.name = name
        self.level = level
        self.metadata = metadata or {}


@pytest.fixture
def state_class():
    return MockState


@pytest.fixture
def builder(state_class):
    return StateBuilder(state_class)


def test_build_state_with_attributes(builder):
    state = (
        builder.add_attribute("name", "TestState")
        .add_attribute("level", 3)
        .add_attribute("metadata", {"key": "value"})
        .build()
    )

    assert state.name == "TestState"
    assert state.level == 3
    assert state.metadata == {"key": "value"}


def test_build_state_without_optional_attributes(builder):
    state = (
        builder.add_attribute("name", "StateWithoutMetadata")
        .add_attribute("level", 1)
        .build()
    )

    assert state.name == "StateWithoutMetadata"
    assert state.level == 1
    assert state.metadata == {}


def test_builder_chaining(builder):
    builder.add_attribute("name", "ChainTest").add_attribute("level", 10)
    state = builder.build()

    assert state.name == "ChainTest"
    assert state.level == 10


def test_overwrite_existing_attribute(builder):
    builder.add_attribute("name", "InitialName")
    builder.add_attribute("name", "OverwrittenName")

    state = builder.add_attribute("level", 5).build()

    assert state.name == "OverwrittenName"
    assert state.level == 5


def test_build_without_required_attributes(builder):
    with pytest.raises(TypeError):
        builder.add_attribute("level", 2).build()


def test_empty_builder(builder):
    with pytest.raises(TypeError):
        builder.build()


def test_reset_builder(builder):
    state1 = (
        builder.add_attribute("name", "FirstState")
        .add_attribute("level", 1)
        .build()
    )

    assert state1.name == "FirstState"
    assert state1.level == 1

    # manual reset (same as original test)
    builder.attributes.clear()

    state2 = (
        builder.add_attribute("name", "SecondState")
        .add_attribute("level", 2)
        .build()
    )

    assert state2.name == "SecondState"
    assert state2.level == 2
