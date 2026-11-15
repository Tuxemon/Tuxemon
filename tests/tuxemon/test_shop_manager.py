# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import pytest

from tuxemon.economy.shop_manager import ShopManager
from tuxemon.item.stock import INFINITE_ITEMS


@pytest.fixture
def manager():
    return ShopManager()


def test_set_and_get_quantity(manager):
    label = manager.get_full_label("economy1", "potion")
    manager.set_quantity(label, 5)
    assert manager.get_quantity(label) == 5


def test_get_or_set_default_creates_entry(manager):
    label = manager.get_full_label("economy1", "elixir")
    qty = manager.get_or_set_default(label, 10)
    assert qty == 10
    assert manager.get_quantity(label) == 10


def test_dump_and_load_roundtrip(manager):
    label = manager.get_full_label("economy1", "ether")
    manager.set_quantity(label, 7)
    dumped = manager.dump_to_dict()
    assert label in dumped
    assert dumped[label]["quantity"] == 7
    reloaded = ShopManager.load_from_dict(dumped)
    assert reloaded.get_quantity(label) == 7


def test_update_existing_quantity(manager):
    label = manager.get_full_label("economy1", "revive")
    manager.set_quantity(label, 3)
    manager.set_quantity(label, 8)
    assert manager.get_quantity(label) == 8


def test_infinite_stock_quantity(manager):
    label = manager.get_full_label("economy1", "infinite_item")
    manager.set_quantity(label, INFINITE_ITEMS)
    assert manager.get_quantity(label) == INFINITE_ITEMS
    assert manager.decrease_stock(label, 10)
    assert manager.get_quantity(label) == INFINITE_ITEMS
    manager.increase_stock(label, 50)
    assert manager.get_quantity(label) == INFINITE_ITEMS


@pytest.mark.parametrize(
    "item, start_qty, decrease, expected_success, expected_final",
    [
        pytest.param("antidote", 5, 3, True, 2, id="decrease_success"),
        pytest.param(
            "rare_candy", 2, 5, False, 2, id="decrease_insufficient_stock"
        ),
    ],
)
def test_decrease_stock(
    manager, item, start_qty, decrease, expected_success, expected_final
):
    label = manager.get_full_label("economy1", item)
    manager.set_quantity(label, start_qty)

    success = manager.decrease_stock(label, decrease)

    assert success is expected_success
    assert manager.get_quantity(label) == expected_final


def test_increase_stock(manager):
    label = manager.get_full_label("economy1", "super_potion")
    manager.set_quantity(label, 4)
    manager.increase_stock(label, 6)
    assert manager.get_quantity(label) == 10


@pytest.mark.parametrize(
    "item, stock, unit_price, buyer_money, expected_max",
    [
        pytest.param("tuxeball", 10, 2, 15, 7, id="finite_stock"),
        pytest.param(
            "ultra_ball", INFINITE_ITEMS, 5, 23, 4, id="infinite_stock"
        ),
    ],
)
def test_get_max_affordable_quantity(
    manager, item, stock, unit_price, buyer_money, expected_max
):
    label = manager.get_full_label("economy1", item)
    manager.set_quantity(label, stock)

    max_qty = manager.get_max_affordable_quantity(
        label, unit_price=unit_price, buyer_money=buyer_money
    )

    assert max_qty == expected_max
