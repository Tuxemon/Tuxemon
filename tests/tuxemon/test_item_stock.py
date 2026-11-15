# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import pytest

from tuxemon.item.stock import INFINITE_ITEMS, Stock


@pytest.mark.parametrize(
    "initial, expected_quantity, expected_infinite",
    [
        pytest.param(1, 1, False, id="init_finite_1"),
        pytest.param(5, 5, False, id="init_finite_5"),
        pytest.param(INFINITE_ITEMS, INFINITE_ITEMS, True, id="init_infinite"),
    ],
)
def test_initialization(initial, expected_quantity, expected_infinite):
    s = Stock(initial)
    assert s.quantity == expected_quantity
    assert s.is_infinite == expected_infinite


@pytest.mark.parametrize(
    "amount, expected",
    [
        pytest.param(10, 10, id="set_positive"),
        pytest.param(0, 0, id="set_zero"),
        pytest.param(-5, 0, id="set_negative_clamped"),
        pytest.param(INFINITE_ITEMS, INFINITE_ITEMS, id="set_infinite"),
    ],
)
def test_set(amount, expected):
    s = Stock()
    s.set(amount)
    assert s.quantity == expected


@pytest.mark.parametrize(
    "initial, add_amount, expected",
    [
        pytest.param(5, 3, 8, id="add_positive"),
        pytest.param(5, 0, 5, id="add_zero"),
        pytest.param(5, -10, 5, id="add_negative_ignored"),
    ],
)
def test_add(initial, add_amount, expected):
    s = Stock(initial)
    s.add(add_amount)
    assert s.quantity == expected


def test_add_to_infinite_does_nothing():
    s = Stock(INFINITE_ITEMS)
    s.add(10)
    assert s.quantity == INFINITE_ITEMS


@pytest.mark.parametrize(
    "initial, remove_amount, expected_success, expected_quantity",
    [
        pytest.param(5, 3, True, 2, id="remove_normal"),
        pytest.param(3, 3, True, 0, id="remove_exact"),
        pytest.param(2, 5, False, 2, id="remove_too_much"),
        pytest.param(5, -1, False, 5, id="remove_negative_invalid"),
    ],
)
def test_remove(initial, remove_amount, expected_success, expected_quantity):
    s = Stock(initial)
    success = s.remove(remove_amount)
    assert success == expected_success
    assert s.quantity == expected_quantity


def test_remove_from_infinite_always_true():
    s = Stock(INFINITE_ITEMS)
    assert s.remove(999999)
    assert s.quantity == INFINITE_ITEMS


@pytest.mark.parametrize(
    "value, expected",
    [
        pytest.param(INFINITE_ITEMS, True, id="infinite_true"),
        pytest.param(0, False, id="zero_not_infinite"),
        pytest.param(10, False, id="finite_not_infinite"),
    ],
)
def test_is_infinite(value, expected):
    s = Stock(value)
    assert s.is_infinite == expected


@pytest.mark.parametrize(
    "quantity, expected",
    [
        pytest.param(INFINITE_ITEMS, True, id="has_any_infinite"),
        pytest.param(0, False, id="has_any_zero"),
        pytest.param(1, True, id="has_any_one"),
        pytest.param(10, True, id="has_any_ten"),
    ],
)
def test_has_any(quantity, expected):
    s = Stock(quantity)
    assert s.has_any == expected


@pytest.mark.parametrize(
    "initial, amount, expected_success, expected_quantity",
    [
        pytest.param(5, 3, True, 8, id="try_add_positive"),
        pytest.param(5, 0, True, 5, id="try_add_zero"),
        pytest.param(5, -1, False, 5, id="try_add_negative_rejected"),
    ],
)
def test_try_add(initial, amount, expected_success, expected_quantity):
    s = Stock(initial)
    success = s.try_add(amount)
    assert success == expected_success
    assert s.quantity == expected_quantity


def test_try_add_infinite():
    s = Stock(INFINITE_ITEMS)
    assert s.try_add(999)
    assert s.quantity == INFINITE_ITEMS


@pytest.mark.parametrize(
    "initial, amount, expected_success, expected_quantity",
    [
        pytest.param(5, 3, True, 2, id="try_remove_normal"),
        pytest.param(5, 5, True, 0, id="try_remove_exact"),
        pytest.param(5, 6, False, 5, id="try_remove_too_much"),
        pytest.param(5, -1, False, 5, id="try_remove_negative_rejected"),
    ],
)
def test_try_remove(initial, amount, expected_success, expected_quantity):
    s = Stock(initial)
    success = s.try_remove(amount)
    assert success == expected_success
    assert s.quantity == expected_quantity


def test_try_remove_infinite():
    s = Stock(INFINITE_ITEMS)
    assert s.try_remove(123456)
    assert s.quantity == INFINITE_ITEMS


def test_consume_one_reduces_quantity():
    s = Stock(3)
    assert s.consume_one()
    assert s.quantity == 2


def test_consume_one_empty_fails():
    s = Stock(0)
    assert not s.consume_one()
    assert s.quantity == 0


def test_consume_one_infinite():
    s = Stock(INFINITE_ITEMS)
    assert s.consume_one()
    assert s.quantity == INFINITE_ITEMS
