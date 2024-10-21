# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
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
            EconomyItemModel(
                item_name="potion", price=20, cost=5, inventory=10
            ),
            EconomyItemModel(item_name="revive", price=100),
            EconomyItemModel(item_name="tuxeball", cost=10),
        ]

    def test_potion_price(self):
        economy = self.economy
        price = economy.lookup_item_price("potion")
        self.assertEqual(price, 20)

    def test_potion_cost(self):
        economy = self.economy
        cost = economy.lookup_item_cost("potion")
        self.assertEqual(cost, 5)

    def test_potion_inventory(self):
        economy = self.economy
        inventory = economy.lookup_item_inventory("potion")
        self.assertEqual(inventory, 10)

    def test_missing_price(self):
        economy = self.economy
        price = economy.lookup_item_price("tuxeball")
        self.assertEqual(price, 0)

    def test_missing_cost(self):
        economy = self.economy
        cost = economy.lookup_item_cost("revive")
        self.assertEqual(cost, 0)

    def test_missing_inventory(self):
        economy = self.economy
        inventory = economy.lookup_item_inventory("revive")
        self.assertEqual(inventory, -1)

    def test_update_item_name(self):
        economy = self.economy
        economy.update_item_field("potion", "item_name", "rubbish")
        name = economy.get_item("rubbish")
        self.assertEqual(name.item_name, "rubbish")

    def test_update_price(self):
        economy = self.economy
        economy.update_item_field("tuxeball", "price", 69)
        price = economy.lookup_item_price("tuxeball")
        self.assertEqual(price, 69)

    def test_update_cost(self):
        economy = self.economy
        economy.update_item_field("revive", "cost", 69)
        cost = economy.lookup_item_cost("revive")
        self.assertEqual(cost, 69)

    def test_update_inventory(self):
        economy = self.economy
        economy.update_item_quantity("revive", 50)
        inventory = economy.lookup_item_inventory("revive")
        self.assertEqual(inventory, 50)

    def test_unknown_item_cost(self):
        economy = self.economy
        with self.assertRaises(RuntimeError):
            economy.lookup_item_cost("unknown_item")

    def test_unknown_item_price(self):
        economy = self.economy
        with self.assertRaises(RuntimeError):
            economy.lookup_item_price("unknown_item")

    def test_unknown_item_inventory(self):
        economy = self.economy
        with self.assertRaises(RuntimeError):
            economy.lookup_item_inventory("unknown_item")
