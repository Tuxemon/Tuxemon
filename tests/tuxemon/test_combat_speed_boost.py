# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
"""
Integration tests: temporary speed boosts affect turn order and damage.

Covers the fix for get_combat_stats() return value being used in both
simple_damage_calculate() and speed_monster() instead of raw base stats.
"""
from unittest.mock import MagicMock

from tuxemon.combat.action_queue import ActionQueue, EnqueuedAction
from tuxemon.formula import simple_damage_calculate, speed_monster
from tuxemon.monster.monster import Monster
from tuxemon.monster.stats import BasicStats
from tuxemon.technique.technique import Technique


def _mock_monster(speed: int = 0, dodge: int = 0, melee: int = 0) -> MagicMock:
    """Create a Monster mock whose get_combat_stats() returns mutable BasicStats."""
    m = MagicMock(spec=Monster)
    m._combat_stats = BasicStats(speed=speed, dodge=dodge, melee=melee)
    m.get_combat_stats.side_effect = lambda: m._combat_stats
    m.status = MagicMock()
    m.status.get_statuses.return_value = []
    return m


def _mock_technique(sort: str = "damage", speed: int = 0) -> MagicMock:
    t = MagicMock(spec=Technique)
    t.sort = sort
    t.speed = speed
    return t


# ---------------------------------------------------------------------------
# speed_monster() uses boosted stats
# ---------------------------------------------------------------------------

def test_speed_monster_uses_combat_stats_not_base():
    """speed_monster() must reflect a temporary speed boost."""
    monster = _mock_monster(speed=10, dodge=0)
    tech = _mock_technique()

    baseline = speed_monster(monster, tech)

    # Simulate a +20 speed boost from a status effect
    monster._combat_stats = BasicStats(speed=30, dodge=0)
    boosted = speed_monster(monster, tech)

    assert boosted > baseline


def test_speed_monster_boost_proportional():
    """A monster with 3× speed from boosts should produce a clearly higher sort key."""
    slow = _mock_monster(speed=10)
    fast_boosted = _mock_monster(speed=30)
    tech = _mock_technique()

    assert speed_monster(fast_boosted, tech) > speed_monster(slow, tech)


# ---------------------------------------------------------------------------
# Mid-turn re-sort: boost to the slowest monster can leapfrog a middle one
# ---------------------------------------------------------------------------

def _make_sorted_queue(monsters_techs: list[tuple[MagicMock, MagicMock]]) -> ActionQueue:
    """Build and sort an ActionQueue from (monster, technique) pairs."""
    q = ActionQueue()
    target = MagicMock(spec=Monster)
    target.is_fainted = False
    for monster, tech in monsters_techs:
        action = EnqueuedAction(user=monster, method=tech, target=target, sub_priority=0.5)
        q.enqueue(action, turn=1)
    q.sort()
    return q


def test_mid_turn_speed_boost_reorders_remaining():
    """
    Scenario: Speed 100 > Speed 90 > Speed 80.
    Speed 100 acts first (highest speed score, popped first).
    Remaining: m90 and m80. Boost m90 to 200; after re-sort m90 should go first.
    """
    m100 = _mock_monster(speed=100)
    m90  = _mock_monster(speed=90)
    m80  = _mock_monster(speed=80)
    tech = _mock_technique(sort="damage")

    q = _make_sorted_queue([(m100, tech), (m90, tech), (m80, tech)])

    first = q.pop()
    assert first.user is m100  # fastest goes first

    # Boost m90 to speed 200; it should now resolve before m80.
    m90._combat_stats = BasicStats(speed=200)
    q.sort()

    second = q.pop()
    third  = q.pop()

    assert second.user is m90   # boosted to fastest among remaining
    assert third.user is m80


def test_no_boost_order_is_stable():
    """Without any boosts, re-sorting an already-sorted queue preserves order."""
    m100 = _mock_monster(speed=100)
    m80  = _mock_monster(speed=80)
    tech = _mock_technique(sort="damage")

    q = _make_sorted_queue([(m100, tech), (m80, tech)])
    order_before = [a.user for a in q.queue]
    q.sort()
    order_after = [a.user for a in q.queue]
    assert order_before == order_after


# ---------------------------------------------------------------------------
# simple_damage_calculate() uses boosted stats
# ---------------------------------------------------------------------------

def test_damage_uses_boosted_melee():
    """A melee boost must increase the damage dealt by a melee technique."""
    from tuxemon.element import Element

    fire = MagicMock(spec=Element)
    fire.slug = "fire"
    fire.lookup_multiplier = MagicMock(return_value=1.0)

    tech = MagicMock()
    tech.range = "melee"
    tech.power = 50
    tech.types.current = [fire]

    target = MagicMock()
    target.types.current = [fire]
    target.get_combat_stats.return_value = BasicStats(armour=10)

    user = _mock_monster(melee=30)
    user.level = 10

    dmg_base, _ = simple_damage_calculate(tech, user, target)

    # Double the melee via a temporary boost
    user._combat_stats = BasicStats(melee=60)
    dmg_boosted, _ = simple_damage_calculate(tech, user, target)

    assert dmg_boosted > dmg_base


def test_damage_uses_boosted_target_armour():
    """A target armour boost must reduce damage received."""
    from tuxemon.element import Element

    fire = MagicMock(spec=Element)
    fire.slug = "fire"
    fire.lookup_multiplier = MagicMock(return_value=1.0)

    tech = MagicMock()
    tech.range = "melee"
    tech.power = 50
    tech.types.current = [fire]

    user = _mock_monster(melee=50)
    user.level = 10

    target = MagicMock()
    target.types.current = [fire]
    target._combat_stats = BasicStats(armour=10)
    target.get_combat_stats.side_effect = lambda: target._combat_stats

    dmg_base, _ = simple_damage_calculate(tech, user, target)

    target._combat_stats = BasicStats(armour=100)
    dmg_armoured, _ = simple_damage_calculate(tech, user, target)

    assert dmg_armoured < dmg_base
