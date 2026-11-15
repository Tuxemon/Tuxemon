# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import pytest

from tuxemon.technique.cooldown import Cooldown


def test_initial_state():
    cd = Cooldown(duration=3)
    assert cd.duration == 3
    assert cd.remaining == 0
    assert cd.is_ready is True
    assert cd.is_recharging is False
    assert cd.multiplier == 1.0
    assert cd.min_remaining == 0
    assert cd.delay_turns == 0
    assert cd.locked is False


@pytest.mark.parametrize(
    "duration",
    [
        pytest.param(0, id="duration_0"),
        pytest.param(1, id="duration_1"),
        pytest.param(5, id="duration_5"),
        pytest.param(999, id="duration_999"),
    ],
)
def test_trigger_sets_remaining_to_duration(duration):
    cd = Cooldown(duration=duration)
    cd.trigger()
    assert cd.remaining == duration
    assert cd.is_recharging is (duration > 0)


@pytest.mark.parametrize(
    "start, tick_amount, expected",
    [
        pytest.param(5, 1, 4, id="tick_1_from_5"),
        pytest.param(5, 2, 3, id="tick_2_from_5"),
        pytest.param(1, 5, 0, id="tick_past_zero"),
        pytest.param(0, 1, 0, id="tick_from_zero"),
    ],
)
def test_tick_reduces_remaining(start, tick_amount, expected):
    cd = Cooldown(duration=10)
    cd.remaining = start
    cd.tick(tick_amount)
    assert cd.remaining == expected


def test_tick_respects_min_remaining():
    cd = Cooldown(duration=10)
    cd.remaining = 5
    cd.min_remaining = 3
    cd.tick(10)
    assert cd.remaining == 3


def test_tick_respects_delay_turns():
    cd = Cooldown(duration=10)
    cd.remaining = 5
    cd.delay_turns = 2

    cd.tick()
    assert cd.remaining == 5
    assert cd.delay_turns == 1

    cd.tick()
    assert cd.remaining == 5
    assert cd.delay_turns == 0

    cd.tick()
    assert cd.remaining == 4


def test_tick_respects_multiplier():
    cd = Cooldown(duration=10)
    cd.remaining = 10
    cd.multiplier = 3.0

    cd.tick()
    assert cd.remaining == 7  # 10 - 3


def test_tick_respects_locked():
    cd = Cooldown(duration=10)
    cd.remaining = 10
    cd.locked = True

    cd.tick()
    assert cd.remaining == 10


@pytest.mark.parametrize(
    "remaining, frozen_turns, ticks, expected_remaining, expected_frozen",
    [
        pytest.param(4, 2, 1, 4, 1, id="frozen_blocks_one_tick"),
        pytest.param(4, 2, 2, 4, 0, id="frozen_blocks_two_ticks"),
        pytest.param(4, 1, 2, 3, 0, id="freeze_expires_then_ticks"),
        pytest.param(4, 0, 1, 3, 0, id="no_freeze_normal_tick"),
    ],
)
def test_freeze_behavior(
    remaining, frozen_turns, ticks, expected_remaining, expected_frozen
):
    cd = Cooldown(duration=5)
    cd.remaining = remaining
    cd.frozen_turns = frozen_turns

    for _ in range(ticks):
        cd.tick()

    assert cd.remaining == expected_remaining
    assert cd.frozen_turns == expected_frozen


@pytest.mark.parametrize(
    "remaining, haste_turns, ticks, expected_remaining, expected_haste",
    [
        pytest.param(6, 2, 1, 4, 1, id="haste_one_tick"),
        pytest.param(6, 2, 2, 2, 0, id="haste_two_ticks"),
        pytest.param(3, 1, 1, 1, 0, id="single_haste_tick"),
        pytest.param(1, 1, 2, 0, 0, id="haste_expires_before_zero"),
    ],
)
def test_haste_behavior(
    remaining, haste_turns, ticks, expected_remaining, expected_haste
):
    cd = Cooldown(duration=5)
    cd.remaining = remaining
    cd.haste_turns = haste_turns

    for _ in range(ticks):
        cd.tick()

    assert cd.remaining == expected_remaining
    assert cd.haste_turns == expected_haste


@pytest.mark.parametrize(
    "initial_remaining, shield, expected_after_trigger, expected_shield",
    [
        pytest.param(10, True, 10, False, id="shield_blocks_and_breaks"),
        pytest.param(10, False, 5, False, id="no_shield_normal_trigger"),
    ],
)
def test_shield_behavior(
    initial_remaining, shield, expected_after_trigger, expected_shield
):
    cd = Cooldown(duration=5)
    cd.remaining = initial_remaining
    cd.shield = shield

    cd.trigger()

    assert cd.remaining == expected_after_trigger
    assert cd.shield == expected_shield


@pytest.mark.parametrize(
    "initial, add_amount, max_value, expected",
    [
        pytest.param(0, 1, 5, 1, id="add_from_zero"),
        pytest.param(1, 2, 5, 3, id="normal_increase"),
        pytest.param(3, 10, 5, 5, id="clamped_overflow"),
        pytest.param(5, 1, 5, 5, id="already_at_max"),
    ],
)
def test_add_increases_remaining_but_clamps(
    initial, add_amount, max_value, expected
):
    cd = Cooldown(duration=3)
    cd.remaining = initial
    cd.add(add_amount, max_value)
    assert cd.remaining == expected


def test_add_respects_locked():
    cd = Cooldown(duration=5)
    cd.remaining = 1
    cd.locked = True
    cd.add(5, 10)
    assert cd.remaining == 1


@pytest.mark.parametrize(
    "initial",
    [
        pytest.param(0, id="initial_0"),
        pytest.param(1, id="initial_1"),
        pytest.param(5, id="initial_5"),
    ],
)
def test_negative_add_does_not_reduce_remaining(initial):
    cd = Cooldown(duration=5)
    cd.remaining = initial
    cd.add(-5, max_value=10)
    assert cd.remaining == initial


@pytest.mark.parametrize(
    "initial,add,expected",
    [
        pytest.param(0, 1, 1, id="start_0_add_1"),
        pytest.param(1, 3, 4, id="start_1_add_3"),
        pytest.param(5, 0, 5, id="start_5_add_0"),
    ],
)
def test_charge_accumulates(initial, add, expected):
    cd = Cooldown(duration=5)
    cd.charge = initial
    cd.charge += add
    assert cd.charge == expected


@pytest.mark.parametrize(
    "remaining,frozen,haste,ticks,expected_remaining",
    [
        pytest.param(5, 1, 2, 1, 5, id="frozen_no_progress"),
        pytest.param(5, 0, 2, 1, 3, id="haste_single_tick"),
        pytest.param(5, 0, 2, 2, 1, id="haste_two_ticks"),
        pytest.param(5, 0, 0, 3, 2, id="no_haste_three_ticks"),
    ],
)
def test_combined_behavior(
    remaining, frozen, haste, ticks, expected_remaining
):
    cd = Cooldown(duration=5)
    cd.remaining = remaining
    cd.frozen_turns = frozen
    cd.haste_turns = haste

    for _ in range(ticks):
        cd.tick()

    assert cd.remaining == expected_remaining


def test_locked_blocks_trigger():
    cd = Cooldown(duration=5)
    cd.remaining = 0
    cd.locked = True
    cd.trigger()
    assert cd.remaining == 0


def test_locked_blocks_tick():
    cd = Cooldown(duration=5)
    cd.remaining = 5
    cd.locked = True
    cd.tick()
    assert cd.remaining == 5


def test_locked_blocks_reset():
    cd = Cooldown(duration=5)
    cd.remaining = 5
    cd.locked = True
    cd.reset()
    assert cd.remaining == 5


def test_delay_prevents_trigger_start():
    cd = Cooldown(duration=5)
    cd.delay_turns = 2
    cd.trigger()
    assert cd.remaining == 0  # delayed


def test_multiplier_tick_scaling():
    cd = Cooldown(duration=10)
    cd.remaining = 10
    cd.multiplier = 2.5
    cd.tick()
    assert cd.remaining == 8  # 10 - int(2.5)


def test_swap_with():
    cd1 = Cooldown(duration=5)
    cd2 = Cooldown(duration=10)

    cd1.remaining = 3
    cd2.remaining = 7

    cd1.frozen_turns = 1
    cd2.haste_turns = 2

    cd1.swap_with(cd2)

    assert cd1.remaining == 7
    assert cd2.remaining == 3
    assert cd1.haste_turns == 2
    assert cd2.frozen_turns == 1
