# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
"""
Tests for held item element resistances (element mantles).

Covers held_item_resistance_multiplier(), apply_held_item_resistance(),
their integration in simple_damage_calculate(), the ItemModel validator for
element_resistances, and the shipped mantle data.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from tuxemon.database.rules import config_combat
from tuxemon.db import ItemModel
from tuxemon.element import Element, ElementTypesHandler
from tuxemon.formula import (
    apply_held_item_resistance,
    held_item_resistance_multiplier,
    simple_damage_calculate,
)
from tuxemon.monster.stats import BasicStats

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ITEM_FOLDER = PROJECT_ROOT / "mods/tuxemon/db/item"
ELEMENT_FOLDER = PROJECT_ROOT / "mods/tuxemon/db/element"


@pytest.fixture(autouse=True)
def clear_multiplier_cache():
    """The multiplier cache is keyed by slug pair and leaks across tests."""
    ElementTypesHandler.clear_cache()
    yield
    ElementTypesHandler.clear_cache()


def _element(slug: str, multiplier: float = 1.0) -> MagicMock:
    element = MagicMock(spec=Element)
    element.slug = slug
    element.lookup_multiplier = MagicMock(return_value=multiplier)
    return element


def _technique(*elements: MagicMock) -> MagicMock:
    technique = MagicMock()
    technique.types.current = list(elements)
    return technique


def _target(resistances: dict[str, float] | None) -> MagicMock:
    target = MagicMock()
    if resistances is None:
        target.held_item = None
    else:
        target.held_item = MagicMock(element_resistances=resistances)
    return target


# held_item_resistance_multiplier


def test_no_held_item_is_neutral():
    tech = _technique(_element("fire"))
    assert held_item_resistance_multiplier(tech, _target(None)) == 1.0


def test_held_item_without_resistances_is_neutral():
    tech = _technique(_element("fire"))
    assert held_item_resistance_multiplier(tech, _target({})) == 1.0


def test_matching_resistance_applies():
    tech = _technique(_element("fire"))
    assert held_item_resistance_multiplier(tech, _target({"fire": 0.5})) == 0.5


def test_non_matching_resistance_is_neutral():
    tech = _technique(_element("water"))
    assert held_item_resistance_multiplier(tech, _target({"fire": 0.5})) == 1.0


def test_only_matching_elements_of_dual_technique_apply():
    tech = _technique(_element("fire"), _element("water"))
    assert held_item_resistance_multiplier(tech, _target({"fire": 0.5})) == 0.5


def test_multiple_matching_elements_compound():
    tech = _technique(_element("fire"), _element("water"))
    target = _target({"fire": 0.5, "water": 0.5})
    assert held_item_resistance_multiplier(tech, target) == 0.25


def test_technique_without_elements_is_neutral():
    tech = _technique()
    assert held_item_resistance_multiplier(tech, _target({"fire": 0.5})) == 1.0


def test_attacker_types_are_ignored():
    """Only the technique's elements matter, not the user's typing."""
    tech = _technique(_element("normal"))
    target = _target({"fire": 0.5})
    assert held_item_resistance_multiplier(tech, target) == 1.0


# apply_held_item_resistance


def test_apply_returns_multiplier_unchanged_without_resistance():
    tech = _technique(_element("fire"))
    # an out-of-range value proves the neutral path does not clamp
    assert apply_held_item_resistance(10.0, tech, _target(None)) == 10.0


def test_apply_scales_multiplier():
    tech = _technique(_element("fire"))
    assert apply_held_item_resistance(2.0, tech, _target({"fire": 0.5})) == 1.0


def test_apply_clamps_to_minimum():
    min_range, _ = config_combat.multiplier_range
    tech = _technique(_element("fire"))
    result = apply_held_item_resistance(
        min_range, tech, _target({"fire": 0.5})
    )
    assert result == min_range


def test_apply_clamps_to_maximum():
    _, max_range = config_combat.multiplier_range
    tech = _technique(_element("fire"))
    result = apply_held_item_resistance(
        max_range, tech, _target({"fire": 2.0})
    )
    assert result == max_range


def test_apply_logs_change(caplog):
    tech = _technique(_element("fire"))
    with caplog.at_level("DEBUG", logger="tuxemon.formula"):
        apply_held_item_resistance(2.0, tech, _target({"fire": 0.5}))
    assert "Held item resistance: 0.5" in caplog.text


# simple_damage_calculate integration


def _damage_env(resistances: dict[str, float] | None, type_mult: float):
    fire = _element("fire", type_mult)
    water = _element("water")

    tech = MagicMock()
    tech.power = 50
    tech.range = "melee"
    tech.types.current = [fire]

    user = MagicMock()
    user.level = 10
    user.get_combat_stats.return_value = BasicStats(melee=30)
    user.status.get_statuses.return_value = []
    # The attacker holds nothing: an auto-specced MagicMock here would make
    # the element modifier a Mock and the damage value meaningless.
    user.held_item = None

    target = _target(resistances)
    target.types.current = [water]
    target.get_combat_stats.return_value = BasicStats(armour=20)
    target.status.get_statuses.return_value = []
    return tech, user, target


def test_damage_reduced_by_matching_mantle():
    _, plain_mult = simple_damage_calculate(*_damage_env(None, 2.0))
    ElementTypesHandler.clear_cache()
    _, resisted_mult = simple_damage_calculate(
        *_damage_env({"fire": 0.5}, 2.0)
    )
    assert plain_mult == 2.0
    assert resisted_mult == 1.0


def test_damage_value_halved_by_matching_mantle():
    plain_dmg, _ = simple_damage_calculate(*_damage_env(None, 2.0))
    ElementTypesHandler.clear_cache()
    resisted_dmg, _ = simple_damage_calculate(*_damage_env({"fire": 0.5}, 2.0))
    assert resisted_dmg < plain_dmg
    assert resisted_dmg == pytest.approx(plain_dmg / 2, abs=1)


def test_damage_unchanged_by_non_matching_mantle():
    plain = simple_damage_calculate(*_damage_env(None, 2.0))
    ElementTypesHandler.clear_cache()
    other = simple_damage_calculate(*_damage_env({"water": 0.5}, 2.0))
    assert plain == other


def test_damage_multiplier_clamped_with_mantle():
    min_range, _ = config_combat.multiplier_range
    _, mult = simple_damage_calculate(*_damage_env({"fire": 0.5}, min_range))
    assert mult == min_range


# ItemModel.elements_exist validator


@pytest.fixture
def mock_has():
    has = MagicMock()
    has.db_entry.side_effect = lambda table, slug: (
        table == "element" and slug in {"fire", "water"}
    )
    with patch("tuxemon.db.has", new=has):
        yield has


def test_validator_accepts_known_elements(mock_has):
    value = {"fire": 0.5, "water": 2.0}
    assert ItemModel.elements_exist(value) == value
    mock_has.db_entry.assert_any_call("element", "fire")
    mock_has.db_entry.assert_any_call("element", "water")


def test_validator_accepts_empty(mock_has):
    assert ItemModel.elements_exist({}) == {}


def test_validator_rejects_unknown_element(mock_has):
    with pytest.raises(ValueError, match="plasma"):
        ItemModel.elements_exist({"plasma": 0.5})


@pytest.mark.parametrize(
    "multiplier",
    [
        pytest.param(0.0, id="zero"),
        pytest.param(-0.5, id="negative"),
    ],
)
def test_validator_rejects_non_positive_multiplier(mock_has, multiplier):
    with pytest.raises(ValueError, match="must be positive"):
        ItemModel.elements_exist({"fire": multiplier})


def test_element_resistances_defaults_to_empty():
    field = ItemModel.model_fields["element_resistances"]
    assert field.default_factory() == {}


# shipped mantle data


ELEMENT_SLUGS = sorted(p.stem for p in ELEMENT_FOLDER.glob("*.yaml"))
MANTLE_FILES = sorted(ITEM_FOLDER.glob("*_mantle.yaml"))
MANTLE_PARAMS = [pytest.param(p, id=p.stem) for p in MANTLE_FILES]


def test_every_element_has_a_mantle():
    mantle_elements = sorted(
        p.stem.removesuffix("_mantle") for p in MANTLE_FILES
    )
    assert mantle_elements == ELEMENT_SLUGS


@pytest.mark.parametrize("path", MANTLE_PARAMS)
def test_mantle_data(path):
    with path.open() as f:
        data = yaml.safe_load(f)
    element = path.stem.removesuffix("_mantle")
    assert data["slug"] == path.stem
    assert data["element_resistances"] == {element: 0.5}
    assert data["behaviors"]["holdable"] is True
    assert data["behaviors"]["consumable"] is False
