# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from tuxemon.core.effects.food_preference import (
    get_bond_from_food,
    is_opposite_taste,
    normalize_taste,
)
from tuxemon.database.rules import config_monster


def monster(taste_warm, taste_cold):
    mon = MagicMock()
    mon.taste_warm = taste_warm
    mon.taste_cold = taste_cold
    return mon


@pytest.mark.parametrize(
    "taste,expected",
    [
        pytest.param("salty", "salty", id="slug_unchanged"),
        pytest.param("taste_salty", "salty", id="prefix_stripped"),
        pytest.param("TASTE_Salty", "salty", id="case_normalized"),
        pytest.param("tasteless", "tasteless", id="tasteless_kept_intact"),
    ],
)
def test_normalize_taste(taste, expected):
    assert normalize_taste(taste) == expected


@pytest.mark.parametrize(
    "taste_a,taste_b,expected",
    [
        pytest.param("salty", "sweet", True, id="opposites"),
        pytest.param("sweet", "salty", True, id="opposites_reversed"),
        pytest.param("taste_salty", "sweet", True, id="mixed_notation"),
        pytest.param("salty", "mild", False, id="unrelated"),
        pytest.param("salty", "hearty", False, id="same_type_never_opposite"),
        pytest.param("salty", "salty", False, id="identical"),
    ],
)
def test_is_opposite_taste(taste_a, taste_b, expected):
    assert is_opposite_taste(taste_a, taste_b) is expected


@pytest.mark.parametrize(
    "taste_warm,taste_cold,warm,cold,expected_key",
    [
        pytest.param("salty", "sweet", "salty", "sweet", "great", id="great"),
        pytest.param(
            "salty", "soft", "salty", "sweet", "good", id="good_warm"
        ),
        pytest.param(
            "hearty", "sweet", "salty", "sweet", "good", id="good_cold"
        ),
        pytest.param(
            "hearty", "mild", "salty", "flakey", "average", id="average"
        ),
        pytest.param("hearty", "sweet", "salty", "mild", "bad", id="bad_warm"),
        pytest.param("hearty", "dry", "zesty", "soft", "bad", id="bad_cold"),
        pytest.param(
            "hearty", "sweet", "salty", "soft", "terrible", id="terrible"
        ),
    ],
)
def test_get_bond_from_food(taste_warm, taste_cold, warm, cold, expected_key):
    target = monster(taste_warm, taste_cold)
    expected = config_monster.bond_preferences[expected_key]
    assert get_bond_from_food(target, warm, cold) == expected


def test_get_bond_from_food_accepts_prefixed_tastes():
    target = monster("salty", "sweet")
    assert (
        get_bond_from_food(target, "taste_salty", "taste_sweet")
        == config_monster.bond_preferences["great"]
    )


def test_get_bond_from_food_unknown_taste_is_average():
    target = monster("hearty", "flakey")
    assert (
        get_bond_from_food(target, "hearty", "pie")
        == (config_monster.bond_preferences["good"])
    )
    assert (
        get_bond_from_food(target, "nonsense", "gibberish")
        == (config_monster.bond_preferences["average"])
    )
