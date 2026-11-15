# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import pytest

from tuxemon.status.lifecycle import Lifecycle


@pytest.mark.parametrize(
    "duration, initial_turn, expected_turn",
    [
        pytest.param(0, 0, 0, id="duration_zero_no_increment"),
        pytest.param(1, 0, 1, id="duration_one_increments"),
        pytest.param(5, 3, 4, id="duration_five_increments"),
    ],
)
def test_tick_turn(duration, initial_turn, expected_turn):
    lc = Lifecycle(duration=duration)
    lc.turn = initial_turn

    lc.tick_turn()

    assert lc.turn == expected_turn


@pytest.mark.parametrize(
    "duration, turn, expected",
    [
        pytest.param(0, 0, False, id="infinite_never_expires"),
        pytest.param(3, 0, False, id="not_exceeded_initial"),
        pytest.param(3, 3, False, id="equal_not_exceeded"),
        pytest.param(3, 4, True, id="exceeded"),
    ],
)
def test_has_exceeded_duration(duration, turn, expected):
    lc = Lifecycle(duration=duration)
    lc.turn = turn

    assert lc.has_exceeded_duration() is expected


@pytest.mark.parametrize(
    "max_uses, increments, expected",
    [
        pytest.param(1, 0, False, id="one_use_not_expired"),
        pytest.param(1, 1, True, id="one_use_expired"),
        pytest.param(2, 1, False, id="two_uses_one_increment"),
        pytest.param(2, 2, True, id="two_uses_two_increments"),
        pytest.param(3, 5, True, id="three_uses_exceeded"),
    ],
)
def test_use_expiration(max_uses, increments, expected):
    lc = Lifecycle()

    for _ in range(increments):
        lc.advance_use()

    assert lc.is_use_expired(max_uses=max_uses) is expected


@pytest.mark.parametrize(
    "initial_stack, max_stacks, expected_new_stack",
    [
        pytest.param(1, 5, 2, id="increment_normal"),
        pytest.param(4, 5, 5, id="increment_to_cap"),
        pytest.param(5, 5, 5, id="already_at_cap"),
        pytest.param(3, 3, 3, id="cap_three"),
    ],
)
def test_stack_increments_and_caps(
    initial_stack, max_stacks, expected_new_stack
):
    lc = Lifecycle(max_stacks=max_stacks)
    lc.stack_level = initial_stack

    old, new = lc.stack()

    assert old == initial_stack
    assert new == expected_new_stack


def test_stack_resets_turn_and_use_counter():
    lc = Lifecycle(max_stacks=5)
    lc.turn = 7
    lc.use_counter = 3

    lc.stack()

    assert lc.turn == 0
    assert lc.use_counter == 0
