# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import pytest

from tuxemon.money.manager import MoneyManager


@pytest.fixture
def money_manager():
    return MoneyManager()


def test_deposit_to_bank(money_manager):
    money_manager.deposit_to_bank(100)
    assert money_manager.bank_account == 100


def test_withdraw_from_bank(money_manager):
    money_manager.deposit_to_bank(100)
    money_manager.withdraw_from_bank(50)
    assert money_manager.bank_account == 50

    with pytest.raises(ValueError):
        money_manager.withdraw_from_bank(100)


def test_get_bank_balance(money_manager):
    money_manager.deposit_to_bank(100)
    assert money_manager.get_bank_balance() == 100


def test_transfer_all_money_to_bank(money_manager):
    money_manager.add_money(100)
    money_manager.transfer_all_money_to_bank()
    assert money_manager.money == 0
    assert money_manager.bank_account == 100


def test_withdraw_all_money_from_bank(money_manager):
    money_manager.deposit_to_bank(100)
    money_manager.withdraw_all_money_from_bank()
    assert money_manager.money == 100
    assert money_manager.bank_account == 0


def test_apply_bank_interest(money_manager):
    money_manager.deposit_to_bank(100)
    money_manager.apply_bank_interest(0.05)
    assert money_manager.bank_account == 105


def test_apply_bank_interest_rounding(money_manager):
    money_manager.deposit_to_bank(99)
    money_manager.apply_bank_interest(0.1)
    assert pytest.approx(money_manager.bank_account, rel=1e-3) == 108
