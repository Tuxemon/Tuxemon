import unittest
from unittest import skip
from unittest.mock import Mock

from tuxemon.item.economy import Economy


class EconomyTestBase(unittest.TestCase):
    pass

class GetDefaultPriceAndCost(EconomyTestBase):
    def setUp(self):
        self.economy = Economy()
        self.economy.slug = "test_economy"
        self.economy.items = [
          {
            "item_name": "potion",
            "price": 20,
            "cost": 5
          },
          {
            "item_name": "revive",
            "price": 100
          },
          {
            "item_name": "capture_device",
            "cost": 10
          }
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
        with self.assertRaises(RuntimeError):
            price = economy.lookup_item_price("capture_device")

    def test_missing_cost(self):
        economy = self.economy
        with self.assertRaises(RuntimeError):
            cost = economy.lookup_item_cost("revive")
