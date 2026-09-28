# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import pytest

from tuxemon.database.rules import config_monster
from tuxemon.db import Acquisition
from tuxemon.monster.bond import BondHandler


@pytest.fixture
def handler():
    return BondHandler()


@pytest.mark.parametrize(
    "value,expected",
    [
        pytest.param(50, 50, id="normal_value"),
        pytest.param(-10, 0, id="below_min_clamped"),
        pytest.param(200, 100, id="above_max_clamped"),
        pytest.param(0, 0, id="at_min"),
        pytest.param(100, 100, id="at_max"),
    ],
)
def test_bond_setter_clamping(handler, value, expected):
    handler.bond = value
    assert handler.bond == expected


@pytest.mark.parametrize(
    "starting,amount,expected_bond",
    [
        pytest.param(50, 10, 60, id="normal_increase"),
        pytest.param(95, 10, 100, id="increase_clamped_at_max"),
        pytest.param(100, 10, 100, id="already_at_max"),
        pytest.param(50, 0, 50, id="increase_by_zero"),
    ],
)
def test_increase_bond(handler, starting, amount, expected_bond):
    handler.bond = starting
    handler.increase_bond(amount)
    assert handler.bond == expected_bond


@pytest.mark.parametrize(
    "starting,amount,milestones,expected_crossed",
    [
        pytest.param(20, 10, [25, 50], {25}, id="crosses_one_milestone"),
        pytest.param(20, 40, [25, 50], {25, 50}, id="crosses_two_milestones"),
        pytest.param(50, 10, [25, 50], set(), id="already_past_milestone"),
        pytest.param(20, 4, [25, 50], set(), id="no_milestone_crossed"),
        pytest.param(20, 10, [], set(), id="no_milestones_configured"),
    ],
)
def test_increase_bond_milestones(
    handler, starting, amount, milestones, expected_crossed
):
    handler.bond = starting
    config_monster.bond_milestones = milestones
    crossed = handler.increase_bond(amount)
    assert crossed == expected_crossed


@pytest.mark.parametrize(
    "acquisition_value,bond_acquisition,expected_bond",
    [
        pytest.param("captured", {"captured": 25}, 25, id="captured"),
        pytest.param("traded", {"traded": 10}, 10, id="traded"),
        pytest.param("unknown", {}, 25, id="missing_uses_default"),
    ],
)
def test_set_bond_for_acquisition(
    handler, acquisition_value, bond_acquisition, expected_bond
):
    config_monster.bond_acquisition = bond_acquisition
    handler.set_bond_for_acquisition(Acquisition(acquisition_value))
    assert handler.bond == expected_bond


@pytest.mark.parametrize(
    "starting,amount,expected_bond",
    [
        pytest.param(50, 10, 40, id="normal_decrease"),
        pytest.param(5, 10, 0, id="decrease_clamped_at_min"),
        pytest.param(0, 10, 0, id="already_at_min"),
        pytest.param(50, 0, 50, id="decrease_by_zero"),
    ],
)
def test_decrease_bond(handler, starting, amount, expected_bond):
    handler.bond = starting
    handler.decrease_bond(amount)
    assert handler.bond == expected_bond


@pytest.mark.parametrize(
    "starting,value,expected_bond",
    [
        pytest.param(50, 10, 60, id="positive_int"),
        pytest.param(50, -10, 40, id="negative_int"),
        pytest.param(50, 0, 50, id="zero_int"),
        pytest.param(50, 0.1, 55, id="positive_float_10_percent"),
        pytest.param(50, -0.1, 45, id="negative_float_10_percent"),
        pytest.param(50, 0.0, 50, id="zero_float"),
        pytest.param(100, 10, 100, id="positive_clamped_at_max"),
        pytest.param(0, -10, 0, id="negative_clamped_at_min"),
    ],
)
def test_change_bond(handler, starting, value, expected_bond):
    handler.bond = starting
    config_monster.bond_milestones = []
    handler.change_bond(value)
    assert handler.bond == expected_bond


def test_change_bond_positive_returns_milestones(handler):
    config_monster.bond_milestones = [30]
    handler.bond = 20
    crossed = handler.change_bond(15)
    assert 30 in crossed


def test_change_bond_negative_returns_empty_set(handler):
    config_monster.bond_milestones = [30]
    handler.bond = 50
    crossed = handler.change_bond(-10)
    assert crossed == set()


@pytest.mark.parametrize(
    "starting,rate,expected_bond",
    [
        pytest.param(100, 0.1, 90, id="normal_decay"),
        pytest.param(10, 0.05, 9, id="small_bond_decay_at_least_1"),
        pytest.param(1, 0.05, 0, id="bond_1_decays_to_0"),
        pytest.param(0, 0.05, 0, id="at_min_no_decay"),
    ],
)
def test_bond_decay(handler, starting, rate, expected_bond):
    handler.bond = starting
    handler.bond_decay(rate)
    assert handler.bond == expected_bond


def test_bond_decay_stops_at_min(handler):
    handler.bond = 0
    handler.bond_decay()
    assert handler.bond == 0


@pytest.mark.parametrize(
    "value,expected",
    [
        pytest.param(100, True, id="at_max"),
        pytest.param(99, False, id="below_max"),
    ],
)
def test_is_max_bond(handler, value, expected):
    handler.bond = value
    assert handler.is_max_bond() == expected


@pytest.mark.parametrize(
    "value,threshold,expected",
    [
        pytest.param(10, 20, True, id="below_threshold"),
        pytest.param(20, 20, True, id="at_threshold"),
        pytest.param(21, 20, False, id="above_threshold"),
    ],
)
def test_is_low_bond(handler, value, threshold, expected):
    handler.bond = value
    assert handler.is_low_bond(threshold) == expected


@pytest.mark.parametrize(
    "save_data,expected_bond",
    [
        pytest.param({"bond_dict": {"bond": 42}}, 42, id="nested_format"),
        pytest.param({"bond": 30}, 30, id="legacy_flat_format"),
        pytest.param({}, 25, id="empty_uses_default"),
        pytest.param({"bond_dict": {"bond": 200}}, 100, id="nested_clamped"),
        pytest.param({"bond": -10}, 0, id="legacy_clamped"),
    ],
)
def test_set_state(save_data, expected_bond):
    h = BondHandler(save_data)
    assert h.bond == expected_bond


def test_get_state(handler):
    handler.bond = 55
    state = handler.get_state()
    assert state == {"bond_dict": {"bond": 55}}


def test_round_trip_state(handler):
    handler.bond = 77
    state = handler.get_state()
    restored = BondHandler(state)
    assert restored.bond == 77


def test_reset_bond(handler):
    handler.bond = 99
    handler.reset_bond()
    assert handler.bond == config_monster.starting_bond


@pytest.mark.parametrize(
    "starting,amount,floor,expected_bond",
    [
        pytest.param(50, 10, None, 40, id="no_floor_uses_min"),
        pytest.param(50, 40, 20, 20, id="floor_prevents_going_below"),
        pytest.param(50, 100, 30, 30, id="floor_clamps_large_decrease"),
        pytest.param(20, 10, 20, 20, id="already_at_floor"),
    ],
)
def test_decrease_bond_with_floor(
    handler, starting, amount, floor, expected_bond
):
    handler.bond = starting
    handler.decrease_bond(amount, floor=floor)
    assert handler.bond == expected_bond


@pytest.mark.parametrize(
    "starting,rate,floor,expected_bond",
    [
        pytest.param(50, 0.1, None, 45, id="no_floor_uses_min"),
        pytest.param(50, 0.5, 30, 30, id="floor_prevents_going_below"),
        pytest.param(30, 0.1, 30, 30, id="already_at_floor_no_decay"),
    ],
)
def test_bond_decay_with_floor(handler, starting, rate, floor, expected_bond):
    handler.bond = starting
    handler.bond_decay(rate, floor=floor)
    assert handler.bond == expected_bond


@pytest.mark.parametrize(
    "starting,value,floor,expected_bond",
    [
        pytest.param(50, -40, 20, 20, id="floor_prevents_negative_change"),
        pytest.param(50, -40, None, 10, id="no_floor_uses_min"),
        pytest.param(20, -10, 20, 20, id="already_at_floor"),
    ],
)
def test_change_bond_with_floor(
    handler, starting, value, floor, expected_bond
):
    handler.bond = starting
    config_monster.bond_milestones = []
    handler.change_bond(value, floor=floor)
    assert handler.bond == expected_bond


@pytest.mark.parametrize(
    "stage_value,stage_floors,expected",
    [
        pytest.param("basic", {"basic": 0, "stage1": 20}, 0, id="basic_floor"),
        pytest.param(
            "stage1", {"basic": 0, "stage1": 20}, 20, id="stage1_floor"
        ),
        pytest.param(
            "stage2", {"basic": 0, "stage1": 20}, 0, id="missing_uses_min"
        ),
    ],
)
def test_get_effective_min_bond(handler, stage_value, stage_floors, expected):
    from tuxemon.db import EvolutionStage

    config_monster.bond_stage_floors = stage_floors
    stage = EvolutionStage(stage_value)
    assert handler.get_effective_min_bond(stage) == expected


@pytest.mark.parametrize(
    "starting,amount,floor,expected_bond",
    [
        pytest.param(30, 5, 40, 30, id="decrease_below_floor_holds_bond"),
        pytest.param(30, 0, 40, 30, id="zero_decrease_below_floor_holds_bond"),
        pytest.param(45, 20, 40, 40, id="decrease_stops_at_floor"),
    ],
)
def test_decrease_bond_never_raises_bond(
    handler, starting, amount, floor, expected_bond
):
    handler.bond = starting
    handler.decrease_bond(amount, floor=floor)
    assert handler.bond == expected_bond


def test_change_bond_below_floor_never_raises_bond(handler):
    handler.bond = 30
    config_monster.bond_milestones = []
    handler.change_bond(-5, floor=40)
    assert handler.bond == 30


def test_bond_decay_below_floor_never_raises_bond(handler):
    handler.bond = 30
    handler.bond_decay(0.5, floor=40)
    assert handler.bond == 30
