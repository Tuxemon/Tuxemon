# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest

from tuxemon.db import EconomyItemModel, EconomyModel
from tuxemon.economy.economy import Economy


class EconomyTestBase(unittest.TestCase):
    def setUp(self):
        self.economy = Economy()
        self.economy.model = EconomyModel(
            slug="test_economy",
            background="gfx/ui/item/item_menu_bg.png",
            resale_multiplier=0.5,
            items=[
                EconomyItemModel(
                    name="potion",
                    price=20,
                    cost=5,
                    inventory=10,
                ),
                EconomyItemModel(name="revive", price=100, cost=0),
                EconomyItemModel(name="tuxeball", price=0, cost=10),
            ],
            monsters=[],
        )

    def test_update_item_field_with_valid_item(self):
        self.economy.update_item_field("potion", "price", 30)
        price = self.economy.lookup_item_field("potion", "price")
        self.assertEqual(price, 30)

    def test_update_item_field_with_unknown_item(self):
        with self.assertRaises(RuntimeError):
            self.economy.update_item_field("unknown_item", "price", 30)

    def test_update_item_quantity_with_valid_item(self):
        self.economy.update_item_quantity("potion", 20)
        inventory = self.economy.lookup_item_field("potion", "inventory")
        self.assertEqual(inventory, 20)

    def test_update_item_quantity_with_unknown_item(self):
        with self.assertRaises(RuntimeError):
            self.economy.update_item_quantity("unknown_item", 20)
