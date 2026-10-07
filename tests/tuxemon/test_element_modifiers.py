# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock

import pytest

from tuxemon.element import Element, ElementTypesHandler
from tuxemon.formula import (
    held_item_element_modifier,
    simple_damage_calculate,
)
from tuxemon.item.item import Item
from tuxemon.monster.stats import BasicStats


@pytest.fixture(autouse=True)
def clear_multiplier_cache():
    """
    ElementTypesHandler memoises multipliers by element slug pair.

    These tests mock lookup_multiplier, so the cache has to be emptied on
    both sides of every test or the mocked values leak into other modules.
    """
    ElementTypesHandler.clear_cache()
    yield
    ElementTypesHandler.clear_cache()


def _element(slug: str) -> MagicMock:
    element = MagicMock(spec=Element)
    element.slug = slug
    element.lookup_multiplier = MagicMock(return_value=1.0)
    return element


def _item(element_modifiers: dict[str, float]) -> MagicMock:
    """A held item mock that runs the real get_element_modifier logic."""
    item = MagicMock(spec=Item)
    item.slug = "test_pellet"
    item.element_modifiers = element_modifiers
    item.get_element_modifier.side_effect = lambda elements: (
        Item.get_element_modifier(item, elements)
    )
    return item


@pytest.fixture
def combat_env():
    """A fire technique, an empty-handed user and a target."""
    tech = MagicMock()
    tech.range = "melee"
    tech.power = 50
    tech.types.current = [_element("fire")]

    user = MagicMock()
    user.level = 10
    user.held_item = None
    user.get_combat_stats.return_value = BasicStats(melee=30)

    target = MagicMock()
    target.types.current = [_element("water")]
    # a bare MagicMock held_item is truthy and its element_resistances is
    # another MagicMock, which is not a usable multiplier
    target.held_item = None
    target.get_combat_stats.return_value = BasicStats(armour=20)

    return tech, user, target


# Item.get_element_modifier


@pytest.mark.parametrize(
    "modifiers, elements, expected",
    [
        pytest.param({}, ["fire"], 1.0, id="item_has_no_modifiers"),
        pytest.param({"fire": 1.2}, ["fire"], 1.2, id="named_element"),
        pytest.param({"fire": 1.2}, ["water"], 1.0, id="other_element"),
        pytest.param({"fire": 1.2}, [], 1.0, id="typeless_technique"),
        pytest.param(
            {"fire": 1.2},
            ["fire", "wood"],
            1.2,
            id="multi_element_one_match",
        ),
        pytest.param(
            {"fire": 1.2, "water": 1.2},
            ["fire", "water"],
            1.2,
            id="multi_element_both_match_applies_once",
        ),
        pytest.param(
            {"fire": 1.2, "water": 1.5},
            ["fire", "water"],
            1.5,
            id="multi_element_strongest_wins",
        ),
    ],
)
def test_get_element_modifier(modifiers, elements, expected):
    item = _item(modifiers)
    result = item.get_element_modifier([_element(e) for e in elements])
    assert result == pytest.approx(expected)


def test_multi_element_match_does_not_compound():
    """Two 1.2x entries must not stack into 1.44x -- nothing clamps this."""
    item = _item({"fire": 1.2, "water": 1.2})
    elements = [_element("fire"), _element("water")]
    assert item.get_element_modifier(elements) == pytest.approx(1.2)


# formula.held_item_element_modifier


def test_held_item_modifier_without_item(combat_env):
    tech, user, _ = combat_env
    assert held_item_element_modifier(tech, user) == 1.0


def test_held_item_modifier_with_matching_item(combat_env):
    tech, user, _ = combat_env
    user.held_item = _item({"fire": 1.2})
    assert held_item_element_modifier(tech, user) == pytest.approx(1.2)


def test_held_item_modifier_with_unrelated_item(combat_env):
    tech, user, _ = combat_env
    user.held_item = _item({"wood": 1.2})
    assert held_item_element_modifier(tech, user) == 1.0


def test_held_item_modifier_with_plain_item(combat_env):
    tech, user, _ = combat_env
    user.held_item = _item({})
    assert held_item_element_modifier(tech, user) == 1.0


def test_pellet_keys_off_technique_not_monster(combat_env):
    """A fire pellet on an earth monster still boosts its fire technique."""
    tech, user, _ = combat_env
    user.types.current = [_element("earth")]
    user.held_item = _item({"fire": 1.2})
    assert held_item_element_modifier(tech, user) == pytest.approx(1.2)


def test_pellet_ignores_the_monsters_own_element(combat_env):
    """An earth pellet does nothing for an earth monster's fire technique."""
    tech, user, _ = combat_env
    user.types.current = [_element("earth")]
    user.held_item = _item({"earth": 1.2})
    assert held_item_element_modifier(tech, user) == 1.0


# simple_damage_calculate integration


def test_damage_unchanged_without_held_item(combat_env):
    tech, user, target = combat_env
    baseline, baseline_mult = simple_damage_calculate(tech, user, target)

    user.held_item = _item({})
    dmg, mult = simple_damage_calculate(tech, user, target)

    assert dmg == baseline
    assert mult == pytest.approx(baseline_mult)


def test_matching_pellet_raises_damage_by_twenty_percent(combat_env):
    # combat_env's stats divide cleanly, so the truncation in
    # simple_damage_calculate cannot hide a rounding error here.
    tech, user, target = combat_env
    baseline, _ = simple_damage_calculate(tech, user, target)

    user.held_item = _item({"fire": 1.2})
    dmg, _ = simple_damage_calculate(tech, user, target)

    assert dmg == int(baseline * 1.2)


def test_pellet_leaves_the_returned_multiplier_alone(combat_env):
    """
    The multiplier feeds config_combat.multiplier_map, an exact-key lookup
    over {4, 2, 0.5, 0.25}, to pick the effectiveness message. A pellet adds
    raw power; folding it in here would push the value off the table and
    silently drop the message.
    """
    tech, user, target = combat_env
    _, baseline_mult = simple_damage_calculate(tech, user, target)

    user.held_item = _item({"fire": 1.2})
    _, mult = simple_damage_calculate(tech, user, target)

    assert mult == pytest.approx(baseline_mult)


def test_unrelated_pellet_leaves_damage_alone(combat_env):
    tech, user, target = combat_env
    baseline, _ = simple_damage_calculate(tech, user, target)

    user.held_item = _item({"wood": 1.2})
    dmg, _ = simple_damage_calculate(tech, user, target)

    assert dmg == baseline


def test_pellet_applies_on_top_of_additional_factors(combat_env):
    tech, user, target = combat_env
    factors = {"weather_bonus": 2.0}
    baseline, baseline_mult = simple_damage_calculate(
        tech, user, target, additional_factors=factors
    )

    user.held_item = _item({"fire": 1.2})
    dmg, mult = simple_damage_calculate(
        tech, user, target, additional_factors=factors
    )

    assert dmg == int(baseline * 1.2)
    assert mult == pytest.approx(baseline_mult)
