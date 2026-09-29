# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock

import pytest
from pydantic_core import ValidationError

from tuxemon.db import Modifier
from tuxemon.element import Element, ElementTypesHandler
from tuxemon.modifiers import ModifiersHandler
from tuxemon.monster.monster import Monster


@pytest.fixture
def elements():
    fire = MagicMock(spec=Element)
    fire.slug = "fire"
    water = MagicMock(spec=Element)
    water.slug = "water"
    grass = MagicMock(spec=Element)
    grass.slug = "grass"
    normal = MagicMock(spec=Element)
    normal.slug = "normal"
    return fire, water, grass, normal


@pytest.fixture
def monster(elements):
    fire, water, grass, normal = elements
    m = MagicMock(spec=Monster)
    m.types = MagicMock(spec=ElementTypesHandler)
    m.types.current = []
    m.tags = []
    m.name = ""
    m.hp_ratio = 1.0
    return m


def test_init():
    modifiers = [Modifier(attribute="type", values=["fire"], multiplier=0.5)]
    handler = ModifiersHandler(modifiers)

    assert handler.list_modifiers() == modifiers
    assert "type" in handler._modifiers
    assert len(handler._modifiers["type"]) == 1


def test_get_modifiers():
    modifiers = [Modifier(attribute="type", values=["fire"], multiplier=0.5)]
    handler = ModifiersHandler(modifiers)
    assert handler.get_modifiers("type") == modifiers


def test_has_modifier():
    modifiers = [Modifier(attribute="type", values=["fire"], multiplier=0.5)]
    handler = ModifiersHandler(modifiers)

    assert handler.has_modifier("type")
    assert not handler.has_modifier("nonexistent")


def test_update_modifier():
    modifiers = [Modifier(attribute="type", values=["fire"], multiplier=0.5)]
    handler = ModifiersHandler(modifiers)

    handler.update_modifier("type", ["water"], 0.8)
    updated = handler.get_modifiers("type")

    assert updated[0].values == ["water"]
    assert updated[0].multiplier == 0.8
    assert all(m.values == ["water"] and m.multiplier == 0.8 for m in updated)


def test_remove_modifier():
    modifiers = [Modifier(attribute="type", values=["fire"], multiplier=0.5)]
    handler = ModifiersHandler(modifiers)

    handler.remove_modifier("type")
    assert not handler.has_modifier("type")


def test_add_modifier():
    modifiers = [Modifier(attribute="type", values=["fire"], multiplier=0.5)]
    handler = ModifiersHandler(modifiers)

    new = Modifier(attribute="type", values=["water"], multiplier=0.8)
    handler.add_modifier(new)

    assert len(handler._modifiers["type"]) == 2


@pytest.mark.parametrize(
    "current_types, expected",
    [
        pytest.param(["fire"], 0.5, id="fire_weak"),
        pytest.param(["water"], 1.0, id="water_neutral"),
    ],
)
def test_weakest_link(elements, monster, current_types, expected):
    fire, water, *_ = elements
    mapping = {"fire": fire, "water": water}

    modifiers = [Modifier(attribute="type", values=["fire"], multiplier=0.5)]
    handler = ModifiersHandler(modifiers)

    monster.types.current = [mapping[t] for t in current_types]
    assert handler.weakest_link(monster) == expected


@pytest.mark.parametrize(
    "current_types, expected",
    [
        pytest.param(["fire"], 0.5, id="fire_weak"),
        pytest.param(["water"], 1.0, id="water_neutral"),
    ],
)
def test_strongest_link(elements, monster, current_types, expected):
    fire, water, *_ = elements
    mapping = {"fire": fire, "water": water}

    modifiers = [Modifier(attribute="type", values=["fire"], multiplier=0.5)]
    handler = ModifiersHandler(modifiers)

    monster.types.current = [mapping[t] for t in current_types]
    assert handler.strongest_link(monster) == expected


@pytest.mark.parametrize(
    "current_types, expected",
    [
        pytest.param(["fire"], 0.5, id="fire_weak"),
        pytest.param(["water"], 1.0, id="water_neutral"),
    ],
)
def test_cumulative_damage(elements, monster, current_types, expected):
    fire, water, *_ = elements
    mapping = {"fire": fire, "water": water}

    modifiers = [Modifier(attribute="type", values=["fire"], multiplier=0.5)]
    handler = ModifiersHandler(modifiers)

    monster.types.current = [mapping[t] for t in current_types]
    assert handler.cumulative_damage(monster) == expected


@pytest.mark.parametrize(
    "current_types, expected",
    [
        pytest.param(["fire"], 0.5, id="fire_weak"),
        pytest.param(["water"], 1.0, id="water_neutral"),
    ],
)
def test_average_damage(elements, monster, current_types, expected):
    fire, water, *_ = elements
    mapping = {"fire": fire, "water": water}

    modifiers = [Modifier(attribute="type", values=["fire"], multiplier=0.5)]
    handler = ModifiersHandler(modifiers)

    monster.types.current = [mapping[t] for t in current_types]
    assert handler.average_damage(monster) == expected


@pytest.mark.parametrize(
    "current_types, expected",
    [
        pytest.param(["fire"], 0.5, id="fire_weak"),
        pytest.param(["water"], 1.0, id="water_neutral"),
    ],
)
def test_first_applicable_damage(elements, monster, current_types, expected):
    fire, water, *_ = elements
    mapping = {"fire": fire, "water": water}

    modifiers = [Modifier(attribute="type", values=["fire"], multiplier=0.5)]
    handler = ModifiersHandler(modifiers)

    monster.types.current = [mapping[t] for t in current_types]
    assert handler.first_applicable_damage(monster) == expected


def test_edge_cases(monster, elements):
    fire, *_ = elements
    handler = ModifiersHandler([])

    monster.types.current = [fire]

    assert handler.weakest_link(monster) == 1.0
    assert handler.strongest_link(monster) == 1.0
    assert handler.cumulative_damage(monster) == 1.0
    assert handler.average_damage(monster) == 1.0
    assert handler.first_applicable_damage(monster) == 1.0


def test_multiple_modifiers(monster, elements):
    fire, water, *_ = elements
    modifiers = [
        Modifier(attribute="type", values=["fire"], multiplier=0.5),
        Modifier(attribute="type", values=["water"], multiplier=0.8),
    ]
    handler = ModifiersHandler(modifiers)

    monster.types.current = [fire, water]

    assert handler.weakest_link(monster) == 0.5
    assert handler.strongest_link(monster) == 0.8
    assert handler.cumulative_damage(monster) == 0.4
    assert handler.average_damage(monster) == 0.65
    assert handler.first_applicable_damage(monster) == 0.5


def test_tag_modifiers(monster):
    modifiers = [Modifier(attribute="tag", values=["tag1"], multiplier=0.5)]
    handler = ModifiersHandler(modifiers)

    monster.tags = ["tag1"]

    assert handler.weakest_link(monster) == 0.5
    assert handler.strongest_link(monster) == 0.5
    assert handler.cumulative_damage(monster) == 0.5
    assert handler.average_damage(monster) == 0.5
    assert handler.first_applicable_damage(monster) == 0.5


def test_invalid_attribute():
    with pytest.raises(ValidationError):
        Modifier(attribute="invalid", values=["fire"], multiplier=0.5)


def test_list_modifiers():
    modifiers = [
        Modifier(attribute="type", values=["fire"], multiplier=0.5),
        Modifier(attribute="type", values=["water"], multiplier=0.8),
    ]
    handler = ModifiersHandler(modifiers)

    assert handler.list_modifiers() == modifiers


def test_turns_expiry(monster, elements):
    fire, water, *_ = elements
    modifiers = [
        Modifier(
            attribute="type",
            values=["fire"],
            multiplier=0.5,
            turns_remaining=1,
        ),
        Modifier(
            attribute="type",
            values=["water"],
            multiplier=0.8,
            turns_remaining=0,
        ),
    ]
    handler = ModifiersHandler(modifiers)

    monster.types.current = [fire, water]

    assert handler.cumulative_damage(monster) == 0.5
    handler.tick_turns()
    assert handler.cumulative_damage(monster) == 1.0


def test_max_stacks_enforced(monster, elements):
    fire, *_ = elements
    modifiers = [
        Modifier(
            attribute="type",
            values=["fire"],
            multiplier=0.5,
            priority=1,
            max_stacks=1,
        ),
        Modifier(
            attribute="type", values=["fire"], multiplier=0.6, priority=0
        ),
    ]
    handler = ModifiersHandler(modifiers)

    monster.types.current = [fire]
    assert handler.cumulative_damage(monster) == 0.5


def test_condition_name_hp_below_50(monster, elements):
    fire, *_ = elements
    modifiers = [
        Modifier(
            attribute="type",
            values=["fire"],
            multiplier=0.5,
            condition_name="hp_below_50",
        ),
    ]
    handler = ModifiersHandler(modifiers)

    monster.types.current = [fire]

    monster.hp_ratio = 0.40
    assert handler.cumulative_damage(monster) == 0.5

    monster.hp_ratio = 0.60
    assert handler.cumulative_damage(monster) == 1.0


def test_remove_expired_modifiers():
    modifiers = [
        Modifier(
            attribute="type",
            values=["fire"],
            multiplier=0.5,
            turns_remaining=0,
        ),
        Modifier(attribute="type", values=["water"], multiplier=0.8),
    ]
    handler = ModifiersHandler(modifiers)

    handler.remove_expired_modifiers()
    remaining = handler.list_modifiers()

    assert len(remaining) == 1
    assert remaining[0].values == ["water"]
