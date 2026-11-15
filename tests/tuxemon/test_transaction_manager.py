# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock, patch

import pytest

from tuxemon.boxes import ItemBoxes
from tuxemon.economy.shop_manager import ShopManager
from tuxemon.economy.transaction import TransactionManager
from tuxemon.entity.bag import BagHandler
from tuxemon.item.item import Item
from tuxemon.item.stock import INFINITE_ITEMS, Stock
from tuxemon.money.manager import MoneyManager
from tuxemon.monster.monster import Monster


def make_test_item(slug: str, qty: int = 1) -> Item:
    item = Item.__new__(Item)
    item.slug = slug
    item.stock = Stock(quantity=qty)
    item.is_infinite = False
    item.is_stackable = True
    return item


class DummyParty:
    def __init__(self):
        self.monsters = []

    def add_monster(self, monster):
        self.monsters.append(monster)

    def remove_monster(self, monster):
        self.monsters.remove(monster)


class DummyNPC:
    def __init__(self):
        self.slug = "dummy"
        self.bag = BagHandler(item_boxes=ItemBoxes(), owner=self)
        self.party = DummyParty()


@pytest.fixture
def tx_env():
    buyer_money = MagicMock(spec=MoneyManager)
    seller_money = MagicMock(spec=MoneyManager)

    shop_manager = ShopManager()
    label = shop_manager.get_full_label("economy1", "potion")
    shop_manager.set_quantity(label, 5)

    tx = TransactionManager(buyer_money, seller_money, shop_manager)

    buyer = DummyNPC()
    seller = DummyNPC()

    item = make_test_item("potion", qty=5)

    monster = MagicMock(spec=Monster)
    return {
        "buyer_money": buyer_money,
        "seller_money": seller_money,
        "shop_manager": shop_manager,
        "label": label,
        "tx": tx,
        "buyer": buyer,
        "seller": seller,
        "item": item,
        "monster": monster,
    }


@patch("tuxemon.economy.transaction.Item.create")
def test_buy_item_reduces_shop_and_buyer_pays(mock_create, tx_env):
    mock_create.return_value = tx_env["item"]
    tx_env["tx"].buy_item(
        tx_env["buyer"], tx_env["item"], 2, tx_env["label"], cost=10
    )
    assert tx_env["shop_manager"].get_quantity(tx_env["label"]) == 3
    assert tx_env["buyer"].bag.find_item("potion").stock.quantity == 2
    tx_env["buyer_money"].remove_money.assert_called_once_with(10)


@patch("tuxemon.economy.transaction.Item.create")
def test_buy_item_infinite_stock(mock_create, tx_env):
    mock_create.return_value = tx_env["item"]
    tx_env["shop_manager"].set_quantity(tx_env["label"], INFINITE_ITEMS)
    tx_env["tx"].buy_item(
        tx_env["buyer"], tx_env["item"], 2, tx_env["label"], cost=5
    )
    assert (
        tx_env["shop_manager"].get_quantity(tx_env["label"]) == INFINITE_ITEMS
    )
    tx_env["buyer_money"].remove_money.assert_called_with(5)


def test_buy_monster(tx_env):
    tx_env["tx"].buy_monster(
        tx_env["buyer"], tx_env["monster"], 1, tx_env["label"], cost=50
    )
    assert tx_env["shop_manager"].get_quantity(tx_env["label"]) == 4
    assert tx_env["monster"] in tx_env["buyer"].party.monsters
    tx_env["buyer_money"].remove_money.assert_called_with(50)


def test_sell_item_increases_shop_and_seller_gets_paid(tx_env):
    tx_env["seller"].bag.add_item(tx_env["item"], 2)
    tx_env["tx"].sell_item(
        tx_env["seller"], tx_env["item"], 1, amount=15, label=tx_env["label"]
    )
    assert tx_env["shop_manager"].get_quantity(tx_env["label"]) == 6
    tx_env["seller_money"].add_money.assert_called_once_with(15)


def test_sell_monster(tx_env):
    tx_env["seller"].party.add_monster(tx_env["monster"])
    tx_env["tx"].sell_monster(
        tx_env["seller"], tx_env["monster"], amount=25, label=tx_env["label"]
    )
    assert tx_env["shop_manager"].get_quantity(tx_env["label"]) == 6
    assert tx_env["monster"] not in tx_env["seller"].party.monsters
    tx_env["seller_money"].add_money.assert_called_once_with(25)


@patch("tuxemon.economy.transaction.Item.create")
def test_buy_item_not_enough_stock(mock_create, tx_env):
    mock_create.return_value = tx_env["item"]
    with pytest.raises(RuntimeError):
        tx_env["tx"].buy_item(
            tx_env["buyer"], tx_env["item"], 10, tx_env["label"], cost=1
        )


def test_sell_item_removes_from_bag(tx_env):
    tx_env["seller"].bag.add_item(tx_env["item"], 1)
    tx_env["tx"].sell_item(
        tx_env["seller"], tx_env["item"], 1, amount=5, label=tx_env["label"]
    )
    assert tx_env["seller"].bag.find_item("potion") is None
