# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import pytest

from tuxemon.money.bill import BillEntry
from tuxemon.money.manager import MoneyManager


@pytest.fixture
def money_manager():
    return MoneyManager()


def test_add_bill(money_manager):
    money_manager.set_bill("bill1", 100)
    assert money_manager.bills == {"bill1": BillEntry(amount=100)}

    money_manager.add_bill("bill1", 50)
    assert money_manager.bills == {"bill1": BillEntry(amount=150)}


def test_remove_bill(money_manager):
    money_manager.set_bill("bill1", 100)
    money_manager.remove_bill("bill1", 50)
    assert money_manager.bills["bill1"].amount == 50

    money_manager.remove_bill("bill1", 50)
    assert money_manager.get_bill("bill1") is None


def test_get_bills(money_manager):
    money_manager.set_bill("bill1", 100)
    money_manager.set_bill("bill2", 50)
    assert money_manager.get_bills() == {
        "bill1": BillEntry(amount=100),
        "bill2": BillEntry(amount=50),
    }


def test_get_bill(money_manager):
    money_manager.set_bill("bill1", 100)
    assert money_manager.get_bill("bill1").amount == 100
    assert money_manager.get_bill("bill2") is None


def test_get_total_bills(money_manager):
    money_manager.set_bill("bill1", 100)
    money_manager.set_bill("bill2", 50)
    assert money_manager.get_total_bills() == 150


@pytest.mark.parametrize(
    "method,attr",
    [
        pytest.param("pay_bill_with_money", "money", id="overpay_with_money"),
        pytest.param(
            "pay_bill_with_deposit", "bank_account", id="overpay_with_deposit"
        ),
    ],
)
def test_overpay_bill(money_manager, method, attr):
    setattr(money_manager, attr, 200)
    money_manager.set_bill("bill1", 100)

    getattr(money_manager, method)("bill1", 150)

    assert getattr(money_manager, attr) == 100
    assert money_manager.get_bill("bill1") is None
