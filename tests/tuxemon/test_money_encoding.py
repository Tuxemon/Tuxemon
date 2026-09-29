# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import pytest

from tuxemon.money.bill import BillEntry
from tuxemon.money.controller import decode_money, encode_money
from tuxemon.money.manager import MoneyManager


@pytest.fixture
def money_manager():
    return MoneyManager()


def test_decode_money():
    json_data = {
        "money": 100,
        "bank_account": 50,
        "bills": {
            "bill1": {"amount": 20},
            "bill2": {"amount": 30},
        },
    }
    mm = decode_money(json_data)

    assert mm.money == 100
    assert mm.bank_account == 50
    assert mm.bills == {
        "bill1": BillEntry(amount=20),
        "bill2": BillEntry(amount=30),
    }


def test_encode_money(money_manager):
    money_manager.add_money(100)
    money_manager.deposit_to_bank(50)
    money_manager.set_bill("bill1", 20)
    money_manager.set_bill("bill2", 30)

    data = encode_money(money_manager)

    assert data == {
        "money": 100,
        "bank_account": 50,
        "bills": {
            "bill1": {"amount": 20},
            "bill2": {"amount": 30},
        },
        "portfolio": {"investments": []},
    }


def test_decode_money_empty():
    mm = decode_money({})
    assert mm.money == 0
    assert mm.bank_account == 0
    assert mm.bills == {}


def test_decode_money_none():
    mm = decode_money(None)
    assert mm.money == 0
    assert mm.bank_account == 0
    assert mm.bills == {}


def test_encode_money_with_interest_and_fee(money_manager):
    money_manager.set_bill("bill1", 100, interest_rate=0.1, late_fee=20)
    data = encode_money(money_manager)

    assert data["bills"]["bill1"]["amount"] == 100
    assert data["bills"]["bill1"]["interest_rate"] == 0.1
    assert data["bills"]["bill1"]["late_fee"] == 20


def test_decode_money_with_interest_and_fee():
    json_data = {
        "money": 0,
        "bank_account": 0,
        "bills": {
            "bill1": {
                "amount": 100,
                "interest_rate": 0.1,
                "late_fee": 20,
            }
        },
    }
    mm = decode_money(json_data)
    bill = mm.get_bill("bill1")

    assert bill.amount == 100
    assert bill.interest_rate == 0.1
    assert bill.late_fee == 20
