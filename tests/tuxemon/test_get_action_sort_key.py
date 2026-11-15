# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock

import pytest

from tuxemon.combat.action_queue import EnqueuedAction
from tuxemon.combat.sort_manager import ActionSortKey, SortManager
from tuxemon.monster.monster import Monster
from tuxemon.technique.technique import Technique


@pytest.fixture
def monster():
    from tuxemon.monster.stats import BasicStats
    m = MagicMock(spec=Monster)
    m.get_combat_stats.return_value = BasicStats(speed=10, dodge=5)
    return m


@pytest.fixture
def tech():
    t = MagicMock(spec=Technique)
    t.speed = 0
    t.sort = "damage"
    return t


def test_none_method(monster):
    action = EnqueuedAction(user=None, method=None, target=monster)
    key = SortManager.get_action_sort_key(action)
    assert isinstance(key, ActionSortKey)
    assert key.primary_order == 0
    assert key.speed == 0
    assert key.tie_breaker == 0.0


def test_none_user(monster, tech):
    action = EnqueuedAction(user=None, method=tech, target=monster)
    key = SortManager.get_action_sort_key(action)
    assert key.primary_order == 0
    assert key.speed == 0
    assert key.tie_breaker == 0.0


@pytest.mark.parametrize(
    "sort_type",
    [
        pytest.param("meta", id="sort_meta"),
        pytest.param("potion", id="sort_potion"),
    ],
)
def test_meta_and_potion_actions(monster, tech, sort_type):
    tech.sort = sort_type
    action = EnqueuedAction(user=monster, method=tech, target=monster)
    key = SortManager.get_action_sort_key(action)
    assert key.primary_order == SortManager.SORT_ORDER.index(sort_type)
    assert key.speed == 0


def test_potion_action_with_none_user(monster, tech):
    tech.sort = "potion"
    action = EnqueuedAction(user=None, method=tech, target=monster)
    key = SortManager.get_action_sort_key(action)
    assert key.primary_order == 0
    assert key.speed == 0


def test_damage_action(monster, tech):
    tech.sort = "damage"
    action = EnqueuedAction(user=monster, method=tech, target=monster)
    key = SortManager.get_action_sort_key(action)
    assert key.primary_order == SortManager.SORT_ORDER.index("damage")
    assert key.speed >= 0


@pytest.mark.parametrize(
    "key,expected",
    [
        pytest.param("potion", 0, id="sort_potion"),
        pytest.param("utility", 1, id="sort_utility"),
        pytest.param("quest", 2, id="sort_quest"),
        pytest.param("meta", 3, id="sort_meta"),
        pytest.param("damage", 4, id="sort_damage"),
        pytest.param("unknown", 5, id="sort_unknown"),
    ],
)
def test_get_sort_index(key, expected):
    assert SortManager.get_sort_index(key) == expected


def test_get_sort_index_with_empty_sort_order():
    class TestSortManager(SortManager):
        SORT_ORDER = []

    assert TestSortManager.get_sort_index("unknown") == 0


@pytest.mark.parametrize(
    "value",
    [
        pytest.param("", id="empty_string"),
        pytest.param("   ", id="whitespace_string"),
    ],
)
def test_get_sort_index_empty_or_whitespace(value):
    assert SortManager.get_sort_index(value) == len(SortManager.SORT_ORDER)
