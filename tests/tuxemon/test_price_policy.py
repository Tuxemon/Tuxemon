# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock

import pytest

from tuxemon.economy.price_policy import (
    PricePolicy,
    PricePolicyData,
    StaticYamlPolicy,
)
from tuxemon.monster.monster import Monster


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
        pytest.param(100, 1, 93, 20, id="base100_qty1"),
        pytest.param(50, 3, 137, 20, id="base50_qty3"),
        pytest.param(100, -1, 93, 20, id="base100_qty_minus1"),
    ],
)
def test_apply_modifiers(policy, base, qty, expected_final, expected_discount):
    final, discount = policy.apply_modifiers(base, qty, "item")
    assert final == expected_final
    assert discount == expected_discount


@pytest.mark.parametrize(
    "base, qty, expected_final, expected_change",
    [
        pytest.param(50, 1, 54, 5, id="resell_base50_qty1"),
        pytest.param(20, 2, 44, 4, id="resell_base20_qty2"),
        pytest.param(100, -1, 107, 5, id="resell_base100_qty_minus1"),
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
        pytest.param("rockitten", 100, 1, 93, 20, id="buy_rockitten_qty1"),
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
        pytest.param("rockitten", 50, 1, 54, 5, id="sell_rockitten_qty1"),
        pytest.param(
            "pairagrin", 20, -1, 23, 4, id="sell_pairagrin_qty_minus1"
        ),
    ],
)
def test_sell_monster_with_policy(
    policy, slug, base, qty, expected_final, expected_change
):
    mock_monster = MagicMock(spec=Monster, slug=slug, name=slug, hp=20)

    final, change = policy.apply_resell_modifiers(base, qty, mock_monster.slug)

    assert final == expected_final
    assert change == expected_change


def test_boundary_conditions(policy):
    # Test 1: Free Item (Base 0)
    # (0 * 1.1 tax) * 0.8 discount + 5 fee = 5
    final_free, _ = policy.apply_modifiers(0, 1, "free-item")
    assert final_free == 5

    # Test 2: 100% Discount (Price should only be the fee)
    data_free = PricePolicyData(
        discount=1.0,
        tax=0.1,
        fee=5,
        resell_bonus=0,
        resell_tax=0,
        seller_fee=0,
    )
    policy_free = StaticYamlPolicy(data_free)
    final_discounted, _ = policy_free.apply_modifiers(100, 1, "gift")
    assert final_discounted == 5
