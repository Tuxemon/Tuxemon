# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock

import pytest

from tuxemon.combat.action_queue import ActionQueue, EnqueuedAction
from tuxemon.monster.monster import Monster
from tuxemon.technique.technique import Technique


@pytest.fixture
def monster():
    m = MagicMock(spec=Monster)
    m.is_fainted = False
    return m


@pytest.fixture
def monster2():
    m = MagicMock(spec=Monster)
    m.is_fainted = False
    return m


@pytest.fixture
def technique():
    t = MagicMock(spec=Technique)
    return t


@pytest.fixture
def action(monster, monster2, technique):
    return EnqueuedAction(monster, technique, monster2)


@pytest.fixture
def queue():
    return ActionQueue()


def test_enqueue_updates_queue_and_history(queue, action):
    queue.enqueue(action, 1)
    assert queue.queue == [action]
    assert queue.history.history == [(1, action)]


def test_dequeue_removes_from_queue_and_history(queue, action):
    queue.enqueue(action, 1)
    queue.dequeue(action)
    assert action not in queue.queue
    assert action not in [a for _, a in queue.history.history]


def test_pop_removes_last_action_and_updates_history(
    queue, monster, monster2, technique
):
    a1 = EnqueuedAction(monster, technique, monster2)
    a2 = EnqueuedAction(monster2, technique, monster)
    queue.enqueue(a1, 1)
    queue.enqueue(a2, 1)
    popped = queue.pop()
    assert popped == a2
    assert a2 not in [a for _, a in queue.history.history]
    assert queue.queue == [a1]


def test_clear_queue_removes_actions_from_history(queue, action):
    queue.enqueue(action, 1)
    queue.clear_queue()
    assert queue.queue == []
    assert queue.history.history == []


def test_clear_history_only_clears_history(queue, action):
    queue.enqueue(action, 1)
    queue.clear_history()
    assert queue.queue == [action]
    assert queue.history.history == []


def test_add_pending_and_move_to_action(queue, action):
    queue.add_pending(action, 2)
    queue.from_pending_to_action(2)
    assert queue.queue == [action]
    assert queue.pending == []


def test_autoclean_pending_removes_fainted(
    queue, monster, monster2, technique
):
    alive = monster
    dead = MagicMock(spec=Monster)
    dead.is_fainted = True
    a1 = EnqueuedAction(alive, technique, alive)
    a2 = EnqueuedAction(dead, technique, alive)
    a3 = EnqueuedAction(alive, technique, dead)
    queue.add_pending(a1, 1)
    queue.add_pending(a2, 1)
    queue.add_pending(a3, 1)
    queue.autoclean_pending()
    assert queue.pending == [(1, a1)]


def test_swap_replaces_targets(queue, monster, monster2, technique):
    action = EnqueuedAction(monster, technique, monster2)
    queue.enqueue(action, 1)
    new_target = MagicMock(spec=Monster)
    queue.swap(monster2, new_target)
    assert queue.queue[0].target == new_target


def test_rewrite_updates_methods(queue, monster, monster2, technique):
    action = EnqueuedAction(monster, technique, monster2)
    queue.enqueue(action, 1)
    new_method = MagicMock(spec=Technique)
    queue.rewrite(monster, new_method)
    assert queue.queue[0].method == new_method


def test_get_last_action_returns_correct(queue, monster, monster2, technique):
    a1 = EnqueuedAction(monster, technique, monster2)
    a2 = EnqueuedAction(monster, technique, monster2)
    queue.enqueue(a1, 1)
    queue.enqueue(a2, 1)
    result = queue.get_last_action(1, monster, "user")
    assert result == a2


def test_get_last_action_returns_none_when_missing(queue, monster):
    assert queue.get_last_action(1, monster, "user") is None


def test_get_all_actions_by_turn(queue, monster, monster2, technique):
    a1 = EnqueuedAction(monster, technique, monster2)
    a2 = EnqueuedAction(monster2, technique, monster)

    queue.enqueue(a1, 1)
    queue.enqueue(a2, 2)

    assert queue.get_all_actions_by_turn(1) == [a1]
    assert queue.get_all_actions_by_turn(2) == [a2]


def test_remove_from_history(queue, action):
    queue.enqueue(action, 1)
    queue.remove_from_history(action)
    assert queue.history.history == []


def test_dequeue_raises_on_missing_action(queue, action):
    with pytest.raises(ValueError):
        queue.dequeue(action)


def test_pop_raises_on_empty_queue(queue):
    with pytest.raises(IndexError):
        queue.pop()


def test_swap_no_match_does_nothing(queue, action, monster):
    queue.enqueue(action, 1)
    queue.swap(MagicMock(), monster)
    assert queue.queue[0] == action


def test_rewrite_no_match_does_nothing(queue, action):
    queue.enqueue(action, 1)
    queue.rewrite(MagicMock(), MagicMock())
    assert queue.queue[0].method == action.method


def test_sort_by_speed(queue):
    fast = MagicMock(spec=Monster)
    fast.speed = 20
    fast.dodge = 0
    fast.is_fainted = False
    fast.get_combat_stats.return_value.speed = 20
    fast.get_combat_stats.return_value.dodge = 0
    slow = MagicMock(spec=Monster)
    slow.speed = 5
    slow.dodge = 0
    slow.is_fainted = False
    slow.get_combat_stats.return_value.speed = 5
    slow.get_combat_stats.return_value.dodge = 0
    tech = MagicMock(spec=Technique)
    tech.sort = "damage"
    tech.priority = 0
    tech.speed = 0
    a_fast = EnqueuedAction(fast, tech, slow)
    a_slow = EnqueuedAction(slow, tech, fast)
    queue.enqueue(a_slow, 1)
    queue.enqueue(a_fast, 1)
    queue.sort()
    assert queue.queue[-1] == a_fast
    assert queue.queue[0] == a_slow


def test_meta_ignores_speed(queue):
    fast = MagicMock(spec=Monster, speed=999, dodge=0, is_fainted=False)
    slow = MagicMock(spec=Monster, speed=1, dodge=0, is_fainted=False)
    meta = MagicMock(spec=Technique, sort="meta")
    a_fast = EnqueuedAction(fast, meta, slow)
    a_slow = EnqueuedAction(slow, meta, fast)
    queue.enqueue(a_fast, 1)
    queue.enqueue(a_slow, 1)
    queue.sort()
    assert queue.queue[0] in (a_fast, a_slow)


def test_pending_moves_then_sorts(queue, monster, monster2, technique):
    slow = MagicMock(spec=Monster)
    slow.speed = 1
    slow.dodge = 0
    slow.is_fainted = False
    slow.get_combat_stats.return_value.speed = 1
    slow.get_combat_stats.return_value.dodge = 0
    fast = MagicMock(spec=Monster)
    fast.speed = 20
    fast.dodge = 0
    fast.is_fainted = False
    fast.get_combat_stats.return_value.speed = 20
    fast.get_combat_stats.return_value.dodge = 0
    technique.sort = "damage"
    technique.speed = 0
    a_slow = EnqueuedAction(slow, technique, fast)
    a_fast = EnqueuedAction(fast, technique, slow)
    queue.add_pending(a_slow, 2)
    queue.enqueue(a_fast, 2)
    queue.from_pending_to_action(2)
    queue.sort()
    assert queue.queue[-1] == a_fast
