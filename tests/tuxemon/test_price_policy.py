# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock

import pytest

from tuxemon.economy.price_policy import (
    PricePolicy,
    PricePolicyData,
    StaticYamlPolicy,
)
from tuxemon.monster import Monster


@pytest.fixture
def policy():
    data = PricePolicyData(
        discount=0.2,  # 20% discount
        tax=0.1,  # 10% tax
        fee=5,  # transaction fee
        resell_bonus=0.1,  # 10% resale bonus
        resell_tax=0.05,  # 5% resale tax
        seller_fee=2,  # seller fee
    )
    return StaticYamlPolicy(data)


@pytest.mark.parametrize(
    "base, qty, expected_final, expected_discount",
    [
        (100, 1, 93, 20),  # Base=100, taxed=110, discounted=88, +fee=93
        (50, 3, 137, 20),  # Base=50, taxed=55, discounted=44, *3=132, +fee=137
        (100, -1, 93, 20),  # Negative qty behaves like -1
    ],
)
def test_apply_modifiers(policy, base, qty, expected_final, expected_discount):
    final, discount = policy.apply_modifiers(base, qty, "item")
    assert final == expected_final
    assert discount == expected_discount


@pytest.mark.parametrize(
    "base, qty, expected_final, expected_change",
    [
        (50, 1, 54, 5),  # Base=50, bonus=55, tax=52.25, +fee=54.25 → 54
        (20, 2, 44, 4),  # Base=20, bonus=22, tax=20.9, *2=41.8, +fee=43.8 → 44
        (100, -1, 107, 5),  # Negative qty behaves like -1
    ],
)
def test_apply_resell_modifiers(
    policy, base, qty, expected_final, expected_change
):
    final, change = policy.apply_resell_modifiers(base, qty, "item")
    assert final == expected_final
    assert change == expected_change


def test_discount_as_dict():
    data = PricePolicyData(
        discount={"item": 0.3, "default": 0.1},
        tax=0.0,
        fee=0,
        resell_bonus=0.0,
        resell_tax=0.0,
        seller_fee=0,
    )
    policy = StaticYamlPolicy(data)
    assert policy.get_discount("item") == 0.3
    assert policy.get_discount("other") == 0.1


def test_zero_values():
    data = PricePolicyData(
        discount=0.0,
        tax=0.0,
        fee=0,
        resell_bonus=0.0,
        resell_tax=0.0,
        seller_fee=0,
    )
    policy = StaticYamlPolicy(data)
    final, discount = policy.apply_modifiers(100, 1, "item")
    assert (final, discount) == (100, 0)
    final, change = policy.apply_resell_modifiers(50, 1, "item")
    assert (final, change) == (50, 0)


def test_base_class_defaults():
    base_policy = PricePolicy()
    assert base_policy.apply_modifiers(100, 1, "item") == (100, 0)
    assert base_policy.apply_resell_modifiers(50, 1, "item") == (50, 0)


@pytest.mark.parametrize(
    "slug, base, qty, expected_final, expected_discount",
    [
        ("rockitten", 100, 1, 93, 20),  # Buying monster
    ],
)
def test_buy_monster_with_policy(
    policy, slug, base, qty, expected_final, expected_discount
):
    mock_monster = MagicMock(spec=Monster, slug=slug, name=slug, hp=100)
    final, discount = policy.apply_modifiers(base, qty, mock_monster.slug)
    assert final == expected_final
    assert discount == expected_discount


@pytest.mark.parametrize(
    "slug, base, qty, expected_final, expected_change",
    [
        ("rockitten", 50, 1, 54, 5),  # Selling monster
        ("pairagrin", 20, -1, 23, 4),  # Selling monster with qty=-1
    ],
)
def test_sell_monster_with_policy(
    policy, slug, base, qty, expected_final, expected_change
):
    mock_monster = MagicMock(spec=Monster, slug=slug, name=slug, hp=20)
    final, change = policy.apply_resell_modifiers(base, qty, mock_monster.slug)
    assert final == expected_final
    assert change == expected_change
