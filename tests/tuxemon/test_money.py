# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest import TestCase
from unittest.mock import MagicMock

from tuxemon.money import (
    BillEntry,
    MoneyController,
    MoneyManager,
    decode_money,
    encode_money,
)


class TestMoneyManager(TestCase):

    def test_init(self):
        money_manager = MoneyManager()
        self.assertEqual(money_manager.money, 0)
        self.assertEqual(money_manager.bank_account, 0)
        self.assertEqual(money_manager.bills, {})

    def test_add_money(self):
        money_manager = MoneyManager()
        money_manager.add_money(100)
        self.assertEqual(money_manager.money, 100)
        money_manager.add_money(-50)
        self.assertEqual(money_manager.money, 50)
        money_manager.add_money(-100)
        self.assertEqual(money_manager.money, 0)

    def test_remove_money(self):
        money_manager = MoneyManager()
        money_manager.add_money(100)
        money_manager.remove_money(50)
        self.assertEqual(money_manager.money, 50)
        money_manager.remove_money(100)
        self.assertEqual(money_manager.money, 0)

    def test_get_money(self):
        money_manager = MoneyManager()
        money_manager.add_money(100)
        self.assertEqual(money_manager.get_money(), 100)

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
        money_manager = MoneyManager()
        money_manager.deposit_to_bank(100)
        self.assertEqual(money_manager.bank_account, 100)

    def test_withdraw_from_bank(self):
        money_manager = MoneyManager()
        money_manager.deposit_to_bank(100)
        money_manager.withdraw_from_bank(50)
        self.assertEqual(money_manager.bank_account, 50)
        with self.assertRaises(ValueError):
            money_manager.withdraw_from_bank(100)

    def test_get_bank_balance(self):
        money_manager = MoneyManager()
        money_manager.deposit_to_bank(100)
        self.assertEqual(money_manager.get_bank_balance(), 100)

    def test_add_bill(self):
        money_manager = MoneyManager()
        money_manager.add_bill("bill1", 100)
        self.assertEqual(money_manager.bills, {"bill1": BillEntry(amount=100)})
        money_manager.add_bill("bill1", 50)
        self.assertEqual(money_manager.bills, {"bill1": BillEntry(amount=150)})

    def test_remove_bill(self):
        money_manager = MoneyManager()
        money_manager.add_bill("bill1", 100)
        money_manager.remove_bill("bill1", 50)
        self.assertEqual(money_manager.bills, {"bill1": BillEntry(amount=50)})
        money_manager.remove_bill("bill1", 50)
        self.assertEqual(money_manager.bills, {"bill1": BillEntry(amount=0)})

    def test_pay_bill_with_money(self):
        money_manager = MoneyManager()
        money_manager.add_money(100)
        money_manager.add_bill("bill1", 50)
        money_manager.pay_bill_with_money("bill1", 50)
        self.assertEqual(money_manager.money, 50)
        self.assertEqual(money_manager.bills, {"bill1": BillEntry(amount=0)})

    def test_pay_bill_with_deposit(self):
        money_manager = MoneyManager()
        money_manager.deposit_to_bank(100)
        money_manager.add_bill("bill1", 50)
        money_manager.pay_bill_with_deposit("bill1", 50)
        self.assertEqual(money_manager.bank_account, 50)
        self.assertEqual(money_manager.bills, {"bill1": BillEntry(amount=0)})

    def test_get_bills(self):
        money_manager = MoneyManager()
        money_manager.add_bill("bill1", 100)
        money_manager.add_bill("bill2", 50)
        self.assertEqual(
            money_manager.get_bills(),
            {"bill1": BillEntry(amount=100), "bill2": BillEntry(amount=50)},
        )

    def test_get_bill(self):
        money_manager = MoneyManager()
        money_manager.add_bill("bill1", 100)
        self.assertEqual(money_manager.get_bill("bill1").amount, 100)
        self.assertEqual(money_manager.get_bill("bill2").amount, 0)

    def test_get_total_bills(self):
        money_manager = MoneyManager()
        money_manager.add_bill("bill1", 100)
        money_manager.add_bill("bill2", 50)
        self.assertEqual(money_manager.get_total_bills(), 150)

    def test_get_total_wealth(self):
        money_manager = MoneyManager()
        money_manager.add_money(100)
        money_manager.deposit_to_bank(50)
        self.assertEqual(money_manager.get_total_wealth(), 150)

    def test_transfer_all_money_to_bank(self):
        money_manager = MoneyManager()
        money_manager.add_money(100)
        money_manager.transfer_all_money_to_bank()
        self.assertEqual(money_manager.money, 0)
        self.assertEqual(money_manager.bank_account, 100)

    def test_withdraw_all_money_from_bank(self):
        money_manager = MoneyManager()
        money_manager.deposit_to_bank(100)
        money_manager.withdraw_all_money_from_bank()
        self.assertEqual(money_manager.money, 100)
        self.assertEqual(money_manager.bank_account, 0)

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
        money_manager = MoneyManager()
        money_manager.add_money(100)
        money_manager.deposit_to_bank(50)
        money_manager.add_bill("bill1", 20)
        money_manager.add_bill("bill2", 30)
        json_data = encode_money(money_manager)
        self.assertEqual(
            json_data,
            {
                "money": 100,
                "bank_account": 50,
                "bills": {
                    "bill1": {"amount": 20},
                    "bill2": {"amount": 30},
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
