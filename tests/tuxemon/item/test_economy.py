# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest

from tuxemon.db import EconomyItemModel
from tuxemon.item.economy import Economy


class EconomyTestBase(unittest.TestCase):
    pass


class GetDefaultPriceAndCost(EconomyTestBase):
    def setUp(self):
        self.economy = Economy()
        self.economy.slug = "test_economy"
        self.economy.items = [
            EconomyItemModel(item_name="potion", price=20, cost=5),
            EconomyItemModel(item_name="revive", price=100),
            EconomyItemModel(item_name="capture_device", cost=10),
        ]

    def test_potion_price(self):
        economy = self.economy
        price = economy.lookup_item_price("potion")
        self.assertEqual(price, 20)

    def test_potion_cost(self):
        economy = self.economy
        cost = economy.lookup_item_cost("potion")
        self.assertEqual(cost, 5)

    def test_missing_price(self):
        economy = self.economy
        price = economy.lookup_item_price("capture_device")
        self.assertEqual(price, 0)

    def test_missing_cost(self):
        economy = self.economy
        cost = economy.lookup_item_cost("revive")
        self.assertEqual(cost, 0)

    def test_unknown_item_price(self):
        economy = self.economy
        with self.assertRaises(RuntimeError):
            cost = economy.lookup_item_cost("unknown_item")

    def test_unknown_item_price(self):
        economy = self.economy
        with self.assertRaises(RuntimeError):
            price = economy.lookup_item_price("unknown_item")
