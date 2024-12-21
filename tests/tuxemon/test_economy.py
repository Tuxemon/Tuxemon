# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest

from tuxemon.db import EconomyItemModel, EconomyModel
from tuxemon.economy import Economy


class EconomyTestBase(unittest.TestCase):
    pass


class GetDefaultPriceAndCost(EconomyTestBase):
    def setUp(self):
        self.economy = Economy()
        self.economy.model = EconomyModel(
            slug="test_economy",
            items=[
                EconomyItemModel(
                    name="potion",
                    price=20,
                    cost=5,
                    inventory=10,
                ),
                EconomyItemModel(name="revive", price=100),
                EconomyItemModel(name="tuxeball", cost=10),
            ],
            monsters=[],
        )

    def test_lookup_item_price_with_valid_item(self):
        price = self.economy.lookup_item_price("potion")
        self.assertEqual(price, 20)

    def test_lookup_item_price_with_missing_price(self):
        price = self.economy.lookup_item_price("tuxeball")
        self.assertEqual(price, 0)

    def test_lookup_item_price_with_unknown_item(self):
        with self.assertRaises(RuntimeError):
            self.economy.lookup_item_price("unknown_item")

    def test_lookup_item_cost_with_valid_item(self):
        cost = self.economy.lookup_item_cost("potion")
        self.assertEqual(cost, 5)

    def test_lookup_item_cost_with_missing_cost(self):
        cost = self.economy.lookup_item_cost("revive")
        self.assertEqual(cost, 0)

    def test_lookup_item_cost_with_unknown_item(self):
        with self.assertRaises(RuntimeError):
            self.economy.lookup_item_cost("unknown_item")

    def test_lookup_item_inventory_with_valid_item(self):
        inventory = self.economy.lookup_item_inventory("potion")
        self.assertEqual(inventory, 10)

    def test_lookup_item_inventory_with_missing_inventory(self):
        inventory = self.economy.lookup_item_inventory("revive")
        self.assertEqual(inventory, -1)

    def test_lookup_item_inventory_with_unknown_item(self):
        with self.assertRaises(RuntimeError):
            self.economy.lookup_item_inventory("unknown_item")

    def test_update_item_field_with_valid_item(self):
        self.economy.update_item_field("potion", "price", 30)
        price = self.economy.lookup_item_price("potion")
        self.assertEqual(price, 30)

    def test_update_item_field_with_unknown_item(self):
        with self.assertRaises(RuntimeError):
            self.economy.update_item_field("unknown_item", "price", 30)

    def test_update_item_quantity_with_valid_item(self):
        self.economy.update_item_quantity("potion", 20)
        inventory = self.economy.lookup_item_inventory("potion")
        self.assertEqual(inventory, 20)

    def test_update_item_quantity_with_unknown_item(self):
        with self.assertRaises(RuntimeError):
            self.economy.update_item_quantity("unknown_item", 20)
