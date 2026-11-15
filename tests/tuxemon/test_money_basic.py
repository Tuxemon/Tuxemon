# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import pytest

from tuxemon.money.manager import MoneyManager


@pytest.fixture
def money_manager():
    return MoneyManager()


def test_init(money_manager):
    assert money_manager.money == 0
    assert money_manager.bank_account == 0
    assert money_manager.bills == {}


@pytest.mark.parametrize(
    "initial,delta,expected",
    [
        pytest.param(0, 100, 100, id="add_from_zero"),
        pytest.param(100, -50, 50, id="add_negative"),
        pytest.param(50, -100, 0, id="add_clamped_to_zero"),
    ],
)
def test_add_money(money_manager, initial, delta, expected):
    money_manager.money = initial
    money_manager.add_money(delta)
    assert money_manager.money == expected


@pytest.mark.parametrize(
    "initial,delta,expected",
    [
        pytest.param(100, 50, 50, id="remove_normal"),
        pytest.param(50, 100, 0, id="remove_clamped_to_zero"),
    ],
)
def test_remove_money(money_manager, initial, delta, expected):
    money_manager.money = initial
    money_manager.remove_money(delta)
    assert money_manager.money == expected


def test_get_money(money_manager):
    money_manager.add_money(100)
    assert money_manager.get_money() == 100
