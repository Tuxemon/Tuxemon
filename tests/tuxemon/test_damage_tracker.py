# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock

import pytest

from tuxemon.combat.damage_tracker import DamageTracker
from tuxemon.monster.monster import Monster


@pytest.fixture
def monsters():
    a = MagicMock(spec=Monster)
    b = MagicMock(spec=Monster)
    c = MagicMock(spec=Monster)
    return a, b, c


@pytest.fixture
def tracker(monsters):
    a, b, c = monsters
    t = DamageTracker()

    # a -> b, 10 damage, turn 1
    t.log_damage(a, b, 10, 1)
    # c -> b, 20 damage, turn 2
    t.log_damage(c, b, 20, 2)
    # a -> b, 30 damage, turn 3
    t.log_damage(a, b, 30, 3)
    # a -> c, 15 damage, turn 1
    t.log_damage(a, c, 15, 1)

    return t


def test_log_damage(tracker, monsters):
    a, b, _ = monsters
    damages = tracker.get_damages(a, b)

    assert len(damages) == 2
    assert damages[0].damage == 10
    assert damages[1].damage == 30


def test_get_damages(tracker, monsters):
    _, b, c = monsters
    damages = tracker.get_damages(c, b)

    assert len(damages) == 1
    assert damages[0].damage == 20


def test_get_all_damages(tracker):
    all_damages = tracker.get_all_damages()
    assert len(all_damages) == 4


def test_remove_monster(tracker, monsters):
    _, b, c = monsters

    tracker.remove_monster(b)
    all_damages = tracker.get_all_damages()

    assert len(all_damages) == 1
    assert all_damages[0].defense == c  # Only a -> c remains


def test_clear_damage(tracker):
    tracker.clear_damage()
    assert tracker.get_all_damages() == []


def test_get_attackers(tracker, monsters):
    a, b, c = monsters
    attackers = tracker.get_attackers(b)

    assert len(attackers) == 2
    assert a in attackers
    assert c in attackers


def test_count_hits(tracker, monsters):
    a, b, _ = monsters
    total_hits, winner_hits = tracker.count_hits(b, a)

    assert total_hits == 3  # hits on b: a->b (2), c->b (1)
    assert winner_hits == 2  # hits by a->b


def test_total_damage_by_attacker(tracker, monsters):
    a, _, c = monsters

    assert tracker.total_damage_by_attacker(a) == 55  # 10 + 30 + 15
    assert tracker.total_damage_by_attacker(c) == 20  # 20
