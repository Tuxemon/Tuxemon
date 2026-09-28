# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock, patch

import pytest

from tuxemon.db import PlagueType
from tuxemon.monster.plague import (
    InoculationResult,
    MonsterPlagueHandler,
    PlagueData,
    config_plagues,
)


@pytest.fixture
def plague_data_basic():
    data = {
        "plague1": PlagueData(spreadness=0.1),
        "plague2": PlagueData(spreadness=0.2),
    }
    config_plagues.update(data)
    return data


@pytest.fixture
def handler(plague_data_basic):
    return MonsterPlagueHandler()


# -----------------------------
# Core Plague Handler Tests
# -----------------------------


def test_init(handler):
    assert handler.current_plagues == {}


def test_infect(handler):
    handler.infect("plague1")
    assert "plague1" in handler.current_plagues
    assert handler.get_plague_type("plague1") == PlagueType.INFECTED


def test_inoculate(handler):
    handler.inoculate("plague1")
    assert "plague1" in handler.current_plagues
    assert handler.get_plague_type("plague1") == PlagueType.INOCULATED


def test_remove_plague(handler):
    handler.infect("plague1")
    handler.remove_plague("plague1")
    assert "plague1" not in handler.current_plagues


def test_clear_plagues(handler):
    handler.infect("plague1")
    handler.inoculate("plague2")
    handler.clear_plagues()
    assert handler.current_plagues == {}


def test_has_plague(handler):
    assert not handler.has_plague("plague1")
    handler.infect("plague1")
    assert handler.has_plague("plague1")


def test_get_plague_type(handler):
    handler.infect("plague1")
    assert handler.get_plague_type("plague1") == PlagueType.INFECTED
    assert handler.get_plague_type("plague2") is None


def test_is_infected(handler):
    assert not handler.is_infected()
    handler.infect("plague1")
    assert handler.is_infected()


def test_is_infected_with(handler):
    handler.infect("plague1")
    assert handler.is_infected_with("plague1")
    assert not handler.is_infected_with("plague2")


def test_is_inoculated_against(handler):
    handler.inoculate("plague1")
    assert handler.is_inoculated_against("plague1")
    assert not handler.is_inoculated_against("plague2")


def test_get_infected_slugs(handler):
    handler.infect("plague1")
    handler.inoculate("plague2")
    assert handler.get_infected_slugs() == ["plague1"]


# -----------------------------
# Dummy Monster Fixture
# -----------------------------


class DummyMonster:
    def __init__(
        self,
        name,
        type_slugs,
        shape_slug,
        weight,
        height,
        status_slug=None,
        plague_data=None,
    ):
        self.name = name
        self.types = MagicMock()
        self.types.get_type_slugs = MagicMock(return_value=type_slugs)

        self.shape = MagicMock()
        self.shape.slug = shape_slug

        self.weight = weight
        self.height = height

        self.status = MagicMock()
        self.status.current_status = MagicMock(
            return_value=MagicMock(slug=status_slug) if status_slug else None
        )

        self.held_item = MagicMock()
        self.plague = MonsterPlagueHandler(plague_data=plague_data or {})


@pytest.fixture
def plague_data_complex():
    data = {
        "test_plague": PlagueData(
            spreadness=1.0,
            type_weights={"wood": 0.6, "poison": 0.4},
            shape_weights={"brute": 0.7, "humanoid": 0.3},
            resistance_modifiers={
                "types": {"fire": 0.5},
                "shapes": {"flier": 0.6},
                "statuses": {"flying": 0.3},
            },
            weight_range=(10.0, 200.0),
            height_range=(0.5, 2.0),
        )
    }
    config_plagues.update(data)
    return data


# -----------------------------
# Infection Logic Tests
# -----------------------------


def test_can_be_infected_by_excluded_by_type_weight(plague_data_complex):
    monster = DummyMonster("FireBrute", ["fire"], "brute", 100.0, 1.5)
    assert not monster.plague.can_be_infected_by(monster, "test_plague")


def test_can_be_infected_by_excluded_by_shape_weight(plague_data_complex):
    monster = DummyMonster("woodflier", ["wood"], "flier", 100.0, 1.5)
    assert not monster.plague.can_be_infected_by(monster, "test_plague")


def test_can_be_infected_by_excluded_by_weight_range(plague_data_complex):
    monster = DummyMonster("Tinywood", ["wood"], "brute", 5.0, 1.5)
    assert not monster.plague.can_be_infected_by(monster, "test_plague")


def test_can_be_infected_by_excluded_by_height_range(plague_data_complex):
    monster = DummyMonster("Tallwood", ["wood"], "brute", 100.0, 3.0)
    assert not monster.plague.can_be_infected_by(monster, "test_plague")


@patch("random.random", return_value=0.999)
def test_can_be_infected_by_with_resistance(_, plague_data_complex):
    monster = DummyMonster(
        "Fireflier", ["fire"], "flier", 100.0, 1.5, "flying"
    )
    plague = plague_data_complex["test_plague"]
    plague.type_weights = {"fire": 1.0}
    plague.shape_weights = {"flier": 1.0}

    assert not monster.plague.can_be_infected_by(monster, "test_plague")


def test_can_be_infected_by_with_no_weights_defined():
    plague = PlagueData(spreadness=1.0)
    config_plagues["simple_plague"] = plague
    monster = DummyMonster("AnyMonster", ["ghost"], "slimy", 100.0, 1.5)
    assert monster.plague.can_be_infected_by(monster, "simple_plague")


@patch("random.random", return_value=0.0)
def test_can_be_infected_by_when_already_infected_simple(
    _, plague_data_complex
):
    monster = DummyMonster("woodBrute", ["wood"], "brute", 100.0, 1.5)
    monster.plague.infect("test_plague")
    assert monster.plague.can_be_infected_by(monster, "test_plague")


@patch("random.random", return_value=0.0)
def test_can_be_infected_by_when_inoculated(_, plague_data_complex):
    monster = DummyMonster(
        "BugBrute",
        ["bug"],
        "brute",
        100.0,
        1.5,
        "sleeping",
        plague_data_complex,
    )
    monster.plague.inoculate("test_plague")
    assert not monster.plague.can_be_infected_by(monster, "test_plague")


@patch("random.random", return_value=0.0)
def test_can_be_infected_by_when_already_infected(_, plague_data_complex):
    monster = DummyMonster(
        "woodBrute",
        ["wood"],
        "brute",
        100.0,
        1.5,
        "sleeping",
        plague_data_complex,
    )
    monster.plague.infect("test_plague")
    assert monster.plague.can_be_infected_by(monster, "test_plague")


# -----------------------------
# Inoculation Tests
# -----------------------------


def test_try_inoculate_success():
    inoc_plague = PlagueData(
        spreadness=0.1,
        inoculation={
            "eligible_types": ["bug"],
            "eligible_shapes": ["humanoid"],
        },
    )
    config_plagues["inoc_plague"] = inoc_plague

    monster = DummyMonster(
        "BugHumanoid",
        ["bug"],
        "humanoid",
        50.0,
        1.0,
        plague_data={"inoc_plague": inoc_plague},
    )

    result = monster.plague.try_inoculate(monster, "inoc_plague")
    assert result == InoculationResult.INOCULATED
    assert monster.plague.is_inoculated_against("inoc_plague")


def test_try_inoculate_ineligible_type():
    inoc_plague = PlagueData(
        spreadness=0.1,
        inoculation={"eligible_types": ["bug"]},
    )
    config_plagues["inoc_plague"] = inoc_plague

    monster = DummyMonster(
        "FireMonster",
        ["fire"],
        "humanoid",
        50.0,
        1.0,
        plague_data={"inoc_plague": inoc_plague},
    )

    result = monster.plague.try_inoculate(monster, "inoc_plague")
    assert result == InoculationResult.NOT_ELIGIBLE


def test_try_inoculate_ineligible_shape():
    inoc_plague = PlagueData(
        spreadness=0.1,
        inoculation={"eligible_shapes": ["humanoid"]},
    )
    config_plagues["inoc_plague"] = inoc_plague

    monster = DummyMonster(
        "BugBrute",
        ["bug"],
        "brute",
        50.0,
        1.0,
        plague_data={"inoc_plague": inoc_plague},
    )

    result = monster.plague.try_inoculate(monster, "inoc_plague")
    assert result == InoculationResult.NOT_ELIGIBLE


def test_try_inoculate_missing_required_item():
    inoc_plague = PlagueData(
        spreadness=0.1,
        inoculation={"required_held_item": "antidote"},
    )
    config_plagues["inoc_plague"] = inoc_plague

    monster = DummyMonster(
        "BugHumanoid",
        ["bug"],
        "humanoid",
        50.0,
        1.0,
        plague_data={"inoc_plague": inoc_plague},
    )
    monster.held_item = None

    result = monster.plague.try_inoculate(monster, "inoc_plague")
    assert result == InoculationResult.NOT_ELIGIBLE


def test_try_inoculate_with_required_item():
    inoc_plague = PlagueData(
        spreadness=0.1,
        inoculation={"required_held_item": "antidote"},
    )
    config_plagues["inoc_plague"] = inoc_plague

    item = MagicMock()
    item.slug = "antidote"

    monster = DummyMonster(
        "BugHumanoid",
        ["bug"],
        "humanoid",
        50.0,
        1.0,
        plague_data={"inoc_plague": inoc_plague},
    )
    monster.held_item = item

    result = monster.plague.try_inoculate(monster, "inoc_plague")
    assert result == InoculationResult.INOCULATED
    assert monster.plague.is_inoculated_against("inoc_plague")
