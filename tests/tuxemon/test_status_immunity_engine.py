# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock

import pytest

from tuxemon.db import BlockedReason
from tuxemon.status.immunity_engine import ImmunityEngine


@pytest.fixture
def engine():
    return ImmunityEngine()


@pytest.fixture
def monster():
    m = MagicMock()
    m.name = "Rockitten"
    return m


@pytest.fixture
def status():
    s = MagicMock()
    s.slug = "burn"
    return s


def test_no_immunity(engine, monster, status):
    monster.held_item = None

    result = engine.check(monster, status)

    assert result.immune is False
    assert result.blocked_by is None
    assert result.reason is None


def test_item_does_not_block(engine, monster, status):
    item = MagicMock()
    item.is_immune.return_value = False
    monster.held_item = item

    result = engine.check(monster, status)

    assert result.immune is False
    assert result.blocked_by is None
    assert result.reason is None
    item.is_immune.assert_called_once_with("burn")


def test_item_blocks(engine, monster, status):
    item = MagicMock()
    item.name = "Fire Charm"
    item.is_immune.return_value = True
    monster.held_item = item

    result = engine.check(monster, status)

    assert result.immune is True
    assert result.blocked_by == "Fire Charm"
    assert result.reason == BlockedReason.IMMUNE_BY_ITEM
    item.is_immune.assert_called_once_with("burn")
