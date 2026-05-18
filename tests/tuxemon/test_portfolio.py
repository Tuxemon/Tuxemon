# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import pytest

from tuxemon.money.portfolio import Investment, PortfolioManager


def test_total_cost_basis_basic():
    inv = Investment(symbol="ROFL", shares=10, purchase_price=150.0)
    assert inv.total_cost_basis == 1500.0


def test_total_cost_basis_rounding():
    inv = Investment(symbol="TGIF", shares=3, purchase_price=333.3333)
    assert inv.total_cost_basis == round(3 * 333.3333, 4)


@pytest.fixture
def pm():
    return PortfolioManager()


def test_buy_new_investment(pm):
    cost = pm.buy_shares("ROFL", 10, 100.0)
    assert cost == 1000.0
    assert "ROFL" in pm.investments
    assert pm.investments["ROFL"].shares == 10


def test_buy_existing_investment(pm):
    pm.buy_shares("ROFL", 10, 100.0)
    pm.buy_shares("ROFL", 10, 200.0)
    inv = pm.investments["ROFL"]
    assert inv.shares == 20
    assert pytest.approx(inv.purchase_price) == 150.0


@pytest.mark.parametrize(
    "symbol",
    [
        pytest.param("$$$", id="invalid_symbol_dollars"),
        pytest.param("###", id="invalid_symbol_hashes"),
    ],
)
def test_buy_invalid_symbol(pm, symbol):
    with pytest.raises(ValueError):
        pm.buy_shares(symbol, 5, 100.0)


@pytest.mark.parametrize(
    "shares, price",
    [
        pytest.param(-5, 100.0, id="negative_shares"),
        pytest.param(5, -100.0, id="negative_price"),
    ],
)
def test_buy_negative_shares_or_price(pm, shares, price):
    with pytest.raises(ValueError):
        pm.buy_shares("ROFL", shares, price)


def test_sell_partial_shares(pm):
    pm.buy_shares("LMAO", 10, 100.0)
    revenue = pm.sell_shares("LMAO", 5, 150.0)
    assert revenue == 750.0
    assert pm.investments["LMAO"].shares == 5


def test_sell_all_shares(pm):
    pm.buy_shares("LMAO", 5, 200.0)
    revenue = pm.sell_shares("LMAO", 5, 250.0)
    assert revenue == 1250.0
    assert "LMAO" not in pm.investments


def test_sell_more_than_owned(pm):
    pm.buy_shares("LMAO", 5, 100.0)
    with pytest.raises(ValueError):
        pm.sell_shares("LMAO", 10, 150.0)


def test_sell_nonexistent_symbol(pm):
    with pytest.raises(KeyError):
        pm.sell_shares("DOGE", 5, 100.0)


def test_sell_invalid_symbol(pm):
    with pytest.raises(ValueError):
        pm.sell_shares("###", 5, 100.0)


def test_sell_negative_shares(pm):
    pm.buy_shares("YOLO", 10, 100.0)
    with pytest.raises(ValueError):
        pm.sell_shares("YOLO", -5, 100.0)


def test_case_insensitive_symbols(pm):
    pm.buy_shares("rofl", 5, 100.0)
    pm.buy_shares("ROFL", 5, 200.0)
    assert pm.investments["ROFL"].shares == 10


def test_multiple_operations_sequence(pm):
    pm.buy_shares("ROFL", 10, 100.0)
    pm.sell_shares("ROFL", 5, 150.0)
    pm.buy_shares("ROFL", 5, 200.0)
    assert pm.investments["ROFL"].shares == 10


def test_portfolio_value_with_prices(pm):
    pm.buy_shares("ROFL", 10, 100.0)
    pm.buy_shares("LMAO", 5, 200.0)
    prices = {"ROFL": 120.0, "LMAO": 250.0}
    assert pm.get_portfolio_value(prices) == 10 * 120.0 + 5 * 250.0


def test_portfolio_value_missing_prices(pm):
    pm.buy_shares("ROFL", 10, 100.0)
    assert pm.get_portfolio_value({}) == 0.0


def test_profit_loss_positive(pm):
    pm.buy_shares("ROFL", 10, 100.0)
    assert pm.calculate_profit_loss({"ROFL": 150.0}) == 500.0


def test_profit_loss_negative(pm):
    pm.buy_shares("ROFL", 10, 100.0)
    assert pm.calculate_profit_loss({"ROFL": 50.0}) == -500.0


def test_profit_loss_zero(pm):
    pm.buy_shares("ROFL", 10, 100.0)
    assert pm.calculate_profit_loss({"ROFL": 100.0}) == 0.0


def test_empty_portfolio_value(pm):
    assert pm.get_portfolio_value({}) == 0.0
    assert pm.calculate_profit_loss({}) == 0.0


def test_get_state_structure(pm):
    pm.buy_shares("ROFL", 10, 100.0)
    state = pm.get_state()
    assert "investments" in state
    assert len(state["investments"]) == 1


def test_from_state_reconstruction():
    state = {
        "investments": [
            {"symbol": "ROFL", "shares": 10, "purchase_price": 100.0},
            {"symbol": "LMAO", "shares": 5, "purchase_price": 200.0},
        ]
    }
    new_pm = PortfolioManager.from_state(state)
    assert new_pm.investments["ROFL"].shares == 10
    assert new_pm.investments["LMAO"].purchase_price == 200.0


def test_from_state_case_insensitivity():
    state = {
        "investments": [
            {"symbol": "rofl", "shares": 10, "purchase_price": 100.0},
        ]
    }
    new_pm = PortfolioManager.from_state(state)
    assert "ROFL" in new_pm.investments
