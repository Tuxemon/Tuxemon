# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import pytest

from tuxemon.money.manager import MoneyManager


@pytest.fixture
def money_manager():
    return MoneyManager()


def test_add_bill_with_interest_and_fee(money_manager):
    money_manager.set_bill("bill1", 100, interest_rate=0.1, late_fee=25)
    bill = money_manager.get_bill("bill1")
    assert bill.amount == 100
    assert bill.interest_rate == 0.1
    assert bill.late_fee == 25


def test_apply_interest_to_bill(money_manager):
    money_manager.set_bill("bill1", 100, interest_rate=0.2)
    money_manager.apply_interest_to_bill("bill1")
    assert money_manager.get_bill("bill1").amount == 120


def test_apply_interest_to_bill_no_rate(money_manager):
    money_manager.set_bill("bill1", 100)
    money_manager.apply_interest_to_bill("bill1")
    assert money_manager.get_bill("bill1").amount == 100


def test_apply_interest_to_nonexistent_bill(money_manager):
    with pytest.raises(KeyError):
        money_manager.apply_interest_to_bill("missing_bill")


def test_apply_late_fee_to_bill(money_manager):
    money_manager.set_bill("bill1", 100, late_fee=15)
    money_manager.apply_late_fee_to_bill("bill1")
    assert money_manager.get_bill("bill1").amount == 115


def test_apply_late_fee_to_bill_no_fee(money_manager):
    money_manager.set_bill("bill1", 100)
    money_manager.apply_late_fee_to_bill("bill1")
    assert money_manager.get_bill("bill1").amount == 100


def test_apply_late_fee_to_nonexistent_bill(money_manager):
    with pytest.raises(KeyError):
        money_manager.apply_late_fee_to_bill("missing_bill")


def test_apply_negative_interest_to_bill(money_manager):
    money_manager.set_bill("bill1", 100, interest_rate=-0.1)
    money_manager.apply_interest_to_bill("bill1")
    assert money_manager.get_bill("bill1").amount == 100


def test_apply_negative_late_fee_to_bill(money_manager):
    money_manager.set_bill("bill1", 100, late_fee=-20)
    money_manager.apply_late_fee_to_bill("bill1")
    assert money_manager.get_bill("bill1").amount == 100


def test_apply_zero_interest_and_fee(money_manager):
    money_manager.set_bill("bill1", 100, interest_rate=None, late_fee=None)
    money_manager.apply_interest_to_bill("bill1")
    money_manager.apply_late_fee_to_bill("bill1")
    assert money_manager.get_bill("bill1").amount == 100


def test_apply_interest_precision(money_manager):
    money_manager.set_bill("bill1", 99.99, interest_rate=0.05)
    money_manager.apply_interest_to_bill("bill1")
    assert (
        pytest.approx(money_manager.get_bill("bill1").amount, rel=1e-3)
        == 103.99
    )


def test_apply_fee_precision(money_manager):
    money_manager.set_bill("bill1", 99.99, late_fee=0.01)
    money_manager.apply_late_fee_to_bill("bill1")
    assert (
        pytest.approx(money_manager.get_bill("bill1").amount, rel=1e-3)
        == 100.00
    )
