# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock

import pytest

from tuxemon.monster.held_item import MonsterItemHandler


@pytest.fixture
def item():
    return MagicMock()


@pytest.fixture
def handler(item):
    return MonsterItemHandler(item)


@pytest.fixture
def empty_handler():
    return MonsterItemHandler()


def test_init(empty_handler):
    assert empty_handler.held_item is None


def test_init_with_item(handler, item):
    assert handler.held_item == item


def test_set_item(empty_handler, item):
    item.behaviors = MagicMock(holdable=True)
    empty_handler.set_item(item)
    assert empty_handler.held_item == item


def test_set_item_not_holdable(empty_handler, item, caplog):
    item.behaviors = MagicMock(holdable=False)
    item.name = "Test Item"

    with caplog.at_level("ERROR"):
        empty_handler.set_item(item)

    assert empty_handler.held_item is None
    assert any("Test Item" in message for message in caplog.messages)


def test_has_item(handler):
    assert handler.has_item()


def test_has_item_none(empty_handler):
    assert not empty_handler.has_item()


def test_clear_item(handler):
    handler.clear_item()
    assert handler.held_item is None


def test_take_item(handler):
    handler.take_item()
    assert handler.held_item is None
