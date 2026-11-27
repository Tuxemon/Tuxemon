# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from unittest.mock import MagicMock

from tuxemon.event.conditions.tuxepedia_caught import (
    TuxepediaCaughtCondition,
)
from tuxemon.tuxepedia.manager import TuxepediaManager


def _session(caught=(), seen=()):
    manager = TuxepediaManager(MagicMock())
    for slug in seen:
        manager.register_seen(slug)
    for slug in caught:
        manager.register_caught(slug)
    session = MagicMock()
    session.player.tuxepedia = manager
    return session


class TestTuxepediaCaughtCondition:
    def test_ten_caught_reaches_ten(self):
        session = _session(caught=[f"m{i}" for i in range(10)])
        cond = TuxepediaCaughtCondition(operator="greater_or_equal", count=10)
        assert cond.test(session) is True

    def test_nine_caught_falls_short(self):
        session = _session(caught=[f"m{i}" for i in range(9)])
        cond = TuxepediaCaughtCondition(operator="greater_or_equal", count=10)
        assert cond.test(session) is False

    def test_seen_only_does_not_count(self):
        session = _session(caught=["a"], seen=["b", "c", "d"])
        cond = TuxepediaCaughtCondition(operator="equals", count=1)
        assert cond.test(session) is True

    def test_same_species_twice_counts_once(self):
        session = _session(caught=["a", "a", "b"])
        cond = TuxepediaCaughtCondition(operator="equals", count=2)
        assert cond.test(session) is True

    def test_empty_tuxepedia(self):
        session = _session()
        cond = TuxepediaCaughtCondition(operator="equals", count=0)
        assert cond.test(session) is True
