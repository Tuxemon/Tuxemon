# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock

import pytest

from tuxemon.combat.action_queue import ActionHistory, EnqueuedAction


@pytest.fixture
def make_action():
    def _make():
        return EnqueuedAction(
            user=MagicMock(), method=MagicMock(), target=MagicMock()
        )

    return _make


@pytest.fixture
def history():
    return ActionHistory()


@pytest.mark.parametrize(
    "turns",
    [
        pytest.param([1], id="single_turn"),
        pytest.param([1, 2], id="two_turns"),
        pytest.param([1, 1, 1], id="three_same_turns"),
        pytest.param([3, 2, 1, 4], id="mixed_turns"),
    ],
)
def test_add_action_and_count(history, make_action, turns):
    for t in turns:
        history.add_action(t, make_action())

    assert history.count_actions() == len(turns)


@pytest.mark.parametrize(
    "turns,query,expected_count",
    [
        pytest.param([1, 1, 2], 1, 2, id="two_matches"),
        pytest.param([2, 2, 2], 2, 3, id="three_matches"),
        pytest.param([1, 2, 3], 4, 0, id="no_matches"),
        pytest.param([5, 5, 5, 1], 5, 3, id="three_of_five"),
    ],
)
def test_get_actions_by_turn(
    history, make_action, turns, query, expected_count
):
    for t in turns:
        history.add_action(t, make_action())

    result = history.get_actions_by_turn(query)
    assert len(result) == expected_count


@pytest.mark.parametrize(
    "turns,start,end,expected_count",
    [
        pytest.param([1, 2, 3], 1, 3, 3, id="full_range"),
        pytest.param([1, 2, 3], 2, 3, 2, id="from_two"),
        pytest.param([1, 2, 3], 3, 3, 1, id="single_value"),
        pytest.param([1, 5, 10], 2, 9, 1, id="middle_only"),
        pytest.param([4, 4, 4], 4, 4, 3, id="all_same"),
        pytest.param([1, 2, 3], 10, 20, 0, id="out_of_range"),
    ],
)
def test_get_actions_by_turn_range(
    history, make_action, turns, start, end, expected_count
):
    for t in turns:
        history.add_action(t, make_action())

    result = history.get_actions_by_turn_range(start, end)
    assert len(result) == expected_count


@pytest.mark.parametrize(
    "turns,expected_index",
    [
        pytest.param([1], 0, id="one_action"),
        pytest.param([1, 2], 1, id="two_actions"),
        pytest.param([5, 5, 5], 2, id="three_same"),
        pytest.param([3, 1, 4, 2], 3, id="mixed_actions"),
    ],
)
def test_get_last_action(history, make_action, turns, expected_index):
    actions = []
    for t in turns:
        a = make_action()
        actions.append(a)
        history.add_action(t, a)
    assert history.get_last_action() == actions[expected_index]


def test_get_last_action_empty(history):
    assert history.get_last_action() is None


def test_clear(history, make_action):
    history.add_action(1, make_action())
    history.add_action(2, make_action())
    history.clear()
    assert history.history == []
    assert history.count_actions() == 0


@pytest.mark.parametrize(
    "turns",
    [
        pytest.param([], id="empty"),
        pytest.param([1], id="one"),
        pytest.param([1, 2], id="two"),
        pytest.param([1, 2, 3, 4], id="four"),
    ],
)
def test_repr_contains_count(history, make_action, turns):
    for t in turns:
        history.add_action(t, make_action())
    rep = repr(history)
    assert "ActionHistory(count=" in rep
    assert "sample=[" in rep


def test_order_preserved(history, make_action):
    a1 = make_action()
    a2 = make_action()
    history.add_action(1, a1)
    history.add_action(1, a2)
    assert history.get_actions_by_turn(1) == [a1, a2]


def test_repr_shows_last_three(history, make_action):
    for i in range(5):
        history.add_action(i, make_action())

    rep = repr(history)
    assert "(2," in rep
    assert "(3," in rep
    assert "(4," in rep
    assert "(0," not in rep
    assert "(1," not in rep
