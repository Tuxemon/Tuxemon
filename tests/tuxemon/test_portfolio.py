# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest

from tuxemon.money.portfolio import Investment, PortfolioManager


class TestInvestment(unittest.TestCase):
    def test_total_cost_basis_basic(self):
        inv = Investment(symbol="ROFL", shares=10, purchase_price=150.0)
        self.assertEqual(inv.total_cost_basis, 1500.0)

    def test_total_cost_basis_rounding(self):
        inv = Investment(symbol="TGIF", shares=3, purchase_price=333.3333)
        self.assertEqual(inv.total_cost_basis, round(3 * 333.3333, 4))


class TestPortfolioManager(unittest.TestCase):
    def setUp(self):
        self.pm = PortfolioManager()

    def test_buy_new_investment(self):
        cost = self.pm.buy_shares("ROFL", 10, 100.0)
        self.assertEqual(cost, 1000.0)
        self.assertIn("ROFL", self.pm.investments)
        self.assertEqual(self.pm.investments["ROFL"].shares, 10)

    def test_buy_existing_investment(self):
        self.pm.buy_shares("ROFL", 10, 100.0)
        self.pm.buy_shares("ROFL", 10, 200.0)
        inv = self.pm.investments["ROFL"]
        self.assertEqual(inv.shares, 20)
        self.assertAlmostEqual(inv.purchase_price, 150.0)

    def test_buy_invalid_symbol(self):
        with self.assertRaises(ValueError):
            self.pm.buy_shares("$$$", 5, 100.0)

    def test_buy_negative_shares_or_price(self):
        with self.assertRaises(ValueError):
            self.pm.buy_shares("ROFL", -5, 100.0)
        with self.assertRaises(ValueError):
            self.pm.buy_shares("ROFL", 5, -100.0)

    def test_sell_partial_shares(self):
        self.pm.buy_shares("LMAO", 10, 100.0)
        revenue = self.pm.sell_shares("LMAO", 5, 150.0)
        self.assertEqual(revenue, 750.0)
        self.assertEqual(self.pm.investments["LMAO"].shares, 5)

    def test_sell_all_shares(self):
        self.pm.buy_shares("LMAO", 5, 200.0)
        revenue = self.pm.sell_shares("LMAO", 5, 250.0)
        self.assertEqual(revenue, 1250.0)
        self.assertNotIn("LMAO", self.pm.investments)

    def test_sell_more_than_owned(self):
        self.pm.buy_shares("LMAO", 5, 100.0)
        with self.assertRaises(ValueError):
            self.pm.sell_shares("LMAO", 10, 150.0)

    def test_sell_nonexistent_symbol(self):
        with self.assertRaises(KeyError):
            self.pm.sell_shares("DOGE", 5, 100.0)

    def test_sell_invalid_symbol(self):
        with self.assertRaises(ValueError):
            self.pm.sell_shares("###", 5, 100.0)

    def test_sell_negative_shares(self):
        self.pm.buy_shares("YOLO", 10, 100.0)
        with self.assertRaises(ValueError):
            self.pm.sell_shares("YOLO", -5, 100.0)

    def test_portfolio_value_with_prices(self):
        self.pm.buy_shares("ROFL", 10, 100.0)
        self.pm.buy_shares("LMAO", 5, 200.0)
        prices = {"ROFL": 120.0, "LMAO": 250.0}
        value = self.pm.get_portfolio_value(prices)
        self.assertEqual(value, 10 * 120.0 + 5 * 250.0)

    def test_portfolio_value_missing_prices(self):
        self.pm.buy_shares("ROFL", 10, 100.0)
        prices = {}
        self.assertEqual(self.pm.get_portfolio_value(prices), 0.0)

    def test_profit_loss_positive(self):
        self.pm.buy_shares("ROFL", 10, 100.0)
        prices = {"ROFL": 150.0}
        self.assertEqual(self.pm.calculate_profit_loss(prices), 500.0)

    def test_profit_loss_negative(self):
        self.pm.buy_shares("ROFL", 10, 100.0)
        prices = {"ROFL": 50.0}
        self.assertEqual(self.pm.calculate_profit_loss(prices), -500.0)

    def test_profit_loss_zero(self):
        self.pm.buy_shares("ROFL", 10, 100.0)
        prices = {"ROFL": 100.0}
        self.assertEqual(self.pm.calculate_profit_loss(prices), 0.0)

    def test_get_state_structure(self):
        self.pm.buy_shares("ROFL", 10, 100.0)
        state = self.pm.get_state()
        self.assertIn("investments", state)
        self.assertEqual(len(state["investments"]), 1)

    def test_from_state_reconstruction(self):
        state = {
            "investments": [
                {"symbol": "ROFL", "shares": 10, "purchase_price": 100.0},
                {"symbol": "LMAO", "shares": 5, "purchase_price": 200.0},
            ]
        }
        new_pm = PortfolioManager.from_state(state)
        self.assertEqual(new_pm.investments["ROFL"].shares, 10)
        self.assertEqual(new_pm.investments["LMAO"].purchase_price, 200.0)

    def test_from_state_case_insensitivity(self):
        state = {
            "investments": [
                {"symbol": "rofl", "shares": 10, "purchase_price": 100.0},
            ]
        }
        new_pm = PortfolioManager.from_state(state)
        self.assertIn("ROFL", new_pm.investments)

    def test_case_insensitive_symbols(self):
        self.pm.buy_shares("rofl", 5, 100.0)
        self.pm.buy_shares("ROFL", 5, 200.0)
        self.assertEqual(self.pm.investments["ROFL"].shares, 10)

    def test_multiple_operations_sequence(self):
        self.pm.buy_shares("ROFL", 10, 100.0)
        self.pm.sell_shares("ROFL", 5, 150.0)
        self.pm.buy_shares("ROFL", 5, 200.0)
        self.assertEqual(self.pm.investments["ROFL"].shares, 10)

    def test_empty_portfolio_value(self):
        self.assertEqual(self.pm.get_portfolio_value({}), 0.0)
        self.assertEqual(self.pm.calculate_profit_loss({}), 0.0)
