# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest import TestCase
from unittest.mock import MagicMock

from tuxemon.money.bill import BillEntry
from tuxemon.money.controller import (
    MoneyController,
    decode_money,
    encode_money,
)
from tuxemon.money.manager import MoneyManager


class TestMoneyManager(TestCase):

    def setUp(self):
        self.money_manager = MoneyManager()

    def test_init(self):
        self.assertEqual(self.money_manager.money, 0)
        self.assertEqual(self.money_manager.bank_account, 0)
        self.assertEqual(self.money_manager.bills, {})

    def test_add_money(self):
        self.money_manager.add_money(100)
        self.assertEqual(self.money_manager.money, 100)
        self.money_manager.add_money(-50)
        self.assertEqual(self.money_manager.money, 50)
        self.money_manager.add_money(-100)
        self.assertEqual(self.money_manager.money, 0)

    def test_remove_money(self):
        self.money_manager.add_money(100)
        self.money_manager.remove_money(50)
        self.assertEqual(self.money_manager.money, 50)
        self.money_manager.remove_money(100)
        self.assertEqual(self.money_manager.money, 0)

    def test_get_money(self):
        self.money_manager.add_money(100)
        self.assertEqual(self.money_manager.get_money(), 100)

    def test_transfer_money_to(self):
        npc1 = MagicMock()
        npc1.money_controller = MoneyController(npc1)
        npc1.money_controller.money_manager = MoneyManager()
        npc2 = MagicMock()
        npc2.money_controller = MoneyController(npc2)
        npc2.money_controller.money_manager = MoneyManager()

        npc1.money_controller.money_manager.add_money(100)
        npc1.money_controller.transfer_money_to(50, npc2)
        self.assertEqual(npc1.money_controller.money_manager.money, 50)
        self.assertEqual(npc2.money_controller.money_manager.money, 50)

    def test_transfer_bank_to(self):
        npc1 = MagicMock()
        npc1.money_controller = MoneyController(npc1)
        npc1.money_controller.money_manager = MoneyManager()
        npc2 = MagicMock()
        npc2.money_controller = MoneyController(npc2)
        npc2.money_controller.money_manager = MoneyManager()

        npc1.money_controller.money_manager.deposit_to_bank(100)
        npc1.money_controller.transfer_bank_to(50, npc2)
        self.assertEqual(npc1.money_controller.money_manager.bank_account, 50)
        self.assertEqual(npc2.money_controller.money_manager.bank_account, 50)

    def test_deposit_to_bank(self):
        self.money_manager.deposit_to_bank(100)
        self.assertEqual(self.money_manager.bank_account, 100)

    def test_withdraw_from_bank(self):
        self.money_manager.deposit_to_bank(100)
        self.money_manager.withdraw_from_bank(50)
        self.assertEqual(self.money_manager.bank_account, 50)
        with self.assertRaises(ValueError):
            self.money_manager.withdraw_from_bank(100)

    def test_get_bank_balance(self):
        self.money_manager.deposit_to_bank(100)
        self.assertEqual(self.money_manager.get_bank_balance(), 100)

    def test_add_bill(self):
        self.money_manager.set_bill("bill1", 100)
        self.assertEqual(
            self.money_manager.bills, {"bill1": BillEntry(amount=100)}
        )
        self.money_manager.add_bill("bill1", 50)
        self.assertEqual(
            self.money_manager.bills, {"bill1": BillEntry(amount=150)}
        )

    def test_remove_bill(self):
        self.money_manager.set_bill("bill1", 100)
        self.money_manager.remove_bill("bill1", -50)
        self.assertEqual(
            self.money_manager.bills, {"bill1": BillEntry(amount=50)}
        )
        self.money_manager.remove_bill("bill1", -50)
        self.assertEqual(
            self.money_manager.bills, {"bill1": BillEntry(amount=0)}
        )

    def test_pay_bill_with_money(self):
        self.money_manager.add_money(100)
        self.money_manager.set_bill("bill1", 50)
        self.money_manager.pay_bill_with_money("bill1", 50)
        self.assertEqual(self.money_manager.money, 50)
        self.assertEqual(
            self.money_manager.bills, {"bill1": BillEntry(amount=0)}
        )

    def test_pay_bill_with_deposit(self):
        self.money_manager.deposit_to_bank(100)
        self.money_manager.set_bill("bill1", 50)
        self.money_manager.pay_bill_with_deposit("bill1", 50)
        self.assertEqual(self.money_manager.bank_account, 50)
        self.assertEqual(
            self.money_manager.bills, {"bill1": BillEntry(amount=0)}
        )

    def test_get_bills(self):
        self.money_manager.set_bill("bill1", 100)
        self.money_manager.set_bill("bill2", 50)
        self.assertEqual(
            self.money_manager.get_bills(),
            {"bill1": BillEntry(amount=100), "bill2": BillEntry(amount=50)},
        )

    def test_get_bill(self):
        self.money_manager.set_bill("bill1", 100)
        self.assertEqual(self.money_manager.get_bill("bill1").amount, 100)
        self.assertIsNone(self.money_manager.get_bill("bill2"))

    def test_get_total_bills(self):
        self.money_manager.set_bill("bill1", 100)
        self.money_manager.set_bill("bill2", 50)
        self.assertEqual(self.money_manager.get_total_bills(), 150)

    def test_get_total_wealth(self):
        self.money_manager.add_money(100)
        self.money_manager.deposit_to_bank(50)
        self.assertEqual(self.money_manager.get_total_wealth(), 150)

    def test_transfer_all_money_to_bank(self):
        self.money_manager.add_money(100)
        self.money_manager.transfer_all_money_to_bank()
        self.assertEqual(self.money_manager.money, 0)
        self.assertEqual(self.money_manager.bank_account, 100)

    def test_withdraw_all_money_from_bank(self):
        self.money_manager.deposit_to_bank(100)
        self.money_manager.withdraw_all_money_from_bank()
        self.assertEqual(self.money_manager.money, 100)
        self.assertEqual(self.money_manager.bank_account, 0)

    def test_decode_money(self):
        json_data = {
            "money": 100,
            "bank_account": 50,
            "bills": {
                "bill1": {"amount": 20},
                "bill2": {"amount": 30},
            },
        }
        money_manager = decode_money(json_data)
        self.assertEqual(money_manager.money, 100)
        self.assertEqual(money_manager.bank_account, 50)
        self.assertEqual(
            money_manager.bills,
            {
                "bill1": BillEntry(amount=20),
                "bill2": BillEntry(amount=30),
            },
        )

    def test_encode_money(self):
        self.money_manager.add_money(100)
        self.money_manager.deposit_to_bank(50)
        self.money_manager.set_bill("bill1", 20)
        self.money_manager.set_bill("bill2", 30)
        json_data = encode_money(self.money_manager)
        self.assertEqual(
            json_data,
            {
                "money": 100,
                "bank_account": 50,
                "bills": {
                    "bill1": {
                        "amount": 20,
                    },
                    "bill2": {
                        "amount": 30,
                    },
                },
            },
        )

    def test_decode_money_empty(self):
        json_data = {}
        money_manager = decode_money(json_data)
        self.assertEqual(money_manager.money, 0)
        self.assertEqual(money_manager.bank_account, 0)
        self.assertEqual(money_manager.bills, {})

    def test_decode_money_none(self):
        json_data = None
        money_manager = decode_money(json_data)
        self.assertEqual(money_manager.money, 0)
        self.assertEqual(money_manager.bank_account, 0)
        self.assertEqual(money_manager.bills, {})

    def test_add_bill_with_interest_and_fee(self):
        self.money_manager.set_bill(
            "bill1", 100, interest_rate=0.1, late_fee=25
        )
        bill = self.money_manager.get_bill("bill1")
        self.assertEqual(bill.amount, 100)
        self.assertEqual(bill.interest_rate, 0.1)
        self.assertEqual(bill.late_fee, 25)

    def test_apply_bank_interest(self):
        self.money_manager.deposit_to_bank(100)
        self.money_manager.apply_bank_interest(0.05)
        self.assertEqual(self.money_manager.bank_account, 105)

    def test_apply_bank_interest_rounding(self):
        self.money_manager.deposit_to_bank(99)
        self.money_manager.apply_bank_interest(0.1)
        self.assertAlmostEqual(self.money_manager.bank_account, 108)

    def test_apply_interest_to_bill(self):
        self.money_manager.set_bill("bill1", 100, interest_rate=0.2)
        self.money_manager.apply_interest_to_bill("bill1")
        self.assertEqual(self.money_manager.get_bill("bill1").amount, 120)

    def test_apply_interest_to_bill_no_rate(self):
        self.money_manager.set_bill("bill1", 100)
        self.money_manager.apply_interest_to_bill("bill1")
        self.assertEqual(self.money_manager.get_bill("bill1").amount, 100)

    def test_apply_interest_to_nonexistent_bill(self):
        with self.assertRaises(KeyError):
            self.money_manager.apply_interest_to_bill("missing_bill")

    def test_apply_late_fee_to_bill(self):
        self.money_manager.set_bill("bill1", 100, late_fee=15)
        self.money_manager.apply_late_fee_to_bill("bill1")
        self.assertEqual(self.money_manager.get_bill("bill1").amount, 115)

    def test_apply_late_fee_to_bill_no_fee(self):
        self.money_manager.set_bill("bill1", 100)
        self.money_manager.apply_late_fee_to_bill("bill1")
        self.assertEqual(self.money_manager.get_bill("bill1").amount, 100)

    def test_apply_late_fee_to_nonexistent_bill(self):
        with self.assertRaises(KeyError):
            self.money_manager.apply_late_fee_to_bill("missing_bill")

    def test_encode_money_with_interest_and_fee(self):
        self.money_manager.set_bill(
            "bill1", 100, interest_rate=0.1, late_fee=20
        )
        json_data = encode_money(self.money_manager)
        self.assertEqual(json_data["bills"]["bill1"]["amount"], 100)
        self.assertEqual(json_data["bills"]["bill1"]["interest_rate"], 0.1)
        self.assertEqual(json_data["bills"]["bill1"]["late_fee"], 20)

    def test_decode_money_with_interest_and_fee(self):
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
        money_manager = decode_money(json_data)
        bill = money_manager.get_bill("bill1")
        self.assertEqual(bill.amount, 100)
        self.assertEqual(bill.interest_rate, 0.1)
        self.assertEqual(bill.late_fee, 20)

    def test_apply_negative_interest_to_bill(self):
        self.money_manager.set_bill("bill1", 100, interest_rate=-0.1)
        self.money_manager.apply_interest_to_bill("bill1")
        self.assertEqual(self.money_manager.get_bill("bill1").amount, 100)

    def test_apply_negative_late_fee_to_bill(self):
        self.money_manager.set_bill("bill1", 100, late_fee=-20)
        self.money_manager.apply_late_fee_to_bill("bill1")
        self.assertEqual(self.money_manager.get_bill("bill1").amount, 100)

    def test_apply_zero_interest_and_fee(self):
        self.money_manager.set_bill(
            "bill1", 100, interest_rate=None, late_fee=None
        )
        self.money_manager.apply_interest_to_bill("bill1")
        self.money_manager.apply_late_fee_to_bill("bill1")
        self.assertEqual(self.money_manager.get_bill("bill1").amount, 100)

    def test_overpay_bill_with_money(self):
        self.money_manager.add_money(200)
        self.money_manager.set_bill("bill1", 100)
        self.money_manager.pay_bill_with_money("bill1", 150)
        self.assertEqual(self.money_manager.money, 100)
        self.assertEqual(self.money_manager.get_bill("bill1").amount, 0)

    def test_overpay_bill_with_deposit(self):
        self.money_manager.deposit_to_bank(200)
        self.money_manager.set_bill("bill1", 100)
        self.money_manager.pay_bill_with_deposit("bill1", 150)
        self.assertEqual(self.money_manager.bank_account, 100)
        self.assertEqual(self.money_manager.get_bill("bill1").amount, 0)

    def test_bill_entry_defaults(self):
        bill = BillEntry(amount=100)
        self.assertEqual(bill.interest_rate, None)
        self.assertEqual(bill.late_fee, None)

    def test_apply_interest_precision(self):
        self.money_manager.set_bill("bill1", 99.99, interest_rate=0.05)
        self.money_manager.apply_interest_to_bill("bill1")
        self.assertAlmostEqual(
            self.money_manager.get_bill("bill1").amount, 103.99
        )

    def test_apply_fee_precision(self):
        self.money_manager.set_bill("bill1", 99.99, late_fee=0.01)
        self.money_manager.apply_late_fee_to_bill("bill1")
        self.assertAlmostEqual(
            self.money_manager.get_bill("bill1").amount, 100.00
        )
