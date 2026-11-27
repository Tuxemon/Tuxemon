# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock, patch

import pytest

from tuxemon.core.asset import init_assets
from tuxemon.db import EffectPhase, ParameterizableRule
from tuxemon.monster.status import MonsterStatusHandler
from tuxemon.status.status import Status

MAX_HP = 96  # divisor 16 -> one dose is 6 HP
DOSE = MAX_HP // 16
FULL_RAMP = [90, 78, 60, 36, 6, 0]  # damage 6, 12, 18, 24, 30, (36)


def make_status(slug, host, duration=0):
    """Build a real Status from a mocked db model (avoids loading the db)."""
    init_assets()
    model = MagicMock()
    model.slug = slug
    model.conditions = []
    model.effects = [ParameterizableRule(type="wasting", parameters=["16"])]
    model.modifiers = []
    model.duration = duration
    model.max_stacks = 5
    model.step_interval = 0
    model.step_effect_value = 0.0
    model.gain_cond = None
    model.use_success = None
    model.use_failure = None
    model.on_positive_status = None
    model.on_negative_status = None
    model.category = None
    with patch("tuxemon.status.status.StatusModel.lookup", return_value=model):
        return Status.create(slug, host)


@pytest.fixture
def session():
    return MagicMock()


@pytest.fixture
def host():
    monster = MagicMock()
    monster.name = "Rockitten"
    monster.hp = MAX_HP
    monster.current_hp = MAX_HP
    monster.is_fainted = False
    monster.held_item = None
    monster.status = MonsterStatusHandler()
    return monster


def gain(session, host, duration=0):
    """Apply wasting the way combat does (it is ticked on acquisition)."""
    host.status.apply_status(session, make_status("wasting", host, duration))
    return host.status.current_status


def play_round(session, status):
    """One round as combat runs it: CombatSession.apply_statuses ticks the
    turn, then CombatState._handle_status performs the status."""
    status.tick_turn()
    return status.use(session, EffectPhase.PERFORM_STATUS)


def play_rounds(session, status, rounds):
    hp = []
    for _ in range(rounds):
        play_round(session, status)
        hp.append(status.host.current_hp)
    return hp


@pytest.mark.parametrize(
    "duration",
    [
        pytest.param(0, id="endless"),
        pytest.param(5, id="short_duration"),
        pytest.param(100, id="long_duration"),
    ],
)
def test_ramps_from_full_hp_and_faints_in_sixth_round(session, host, duration):
    # The turn counter (which only runs with a duration, and is already on
    # turn 2 by the first round) must not affect the ramp.
    status = gain(session, host, duration)

    assert play_rounds(session, status, 6) == FULL_RAMP


@pytest.mark.parametrize(
    "duration",
    [
        pytest.param(0, id="endless"),
        pytest.param(100, id="with_duration"),
    ],
)
def test_first_round_is_a_single_dose(session, host, duration):
    status = gain(session, host, duration)

    result = play_round(session, status)

    assert result.success
    assert host.current_hp == MAX_HP - DOSE


def test_rounds_without_damage_still_count(session, host):
    status = gain(session, host)
    host.is_fainted = True
    results = [play_round(session, status) for _ in range(2)]

    assert not any(result.success for result in results)
    assert host.current_hp == MAX_HP
    assert status.nr_round == 2

    host.is_fainted = False
    play_round(session, status)

    # third round: a triple dose, the skipped rounds were counted
    assert host.current_hp == MAX_HP - 3 * DOSE


def test_stack_restarts_the_ramp_at_a_single_dose(session, host):
    status = gain(session, host)
    play_rounds(session, status, 3)
    host.current_hp = MAX_HP

    # re-applying wasting stacks it
    host.status.apply_status(session, make_status("wasting", host))
    assert host.status.current_status is status

    assert play_rounds(session, status, 2) == [
        MAX_HP - DOSE,
        MAX_HP - 3 * DOSE,
    ]


@pytest.mark.parametrize(
    "phase",
    [
        pytest.param(EffectPhase.ON_START, id="on_start"),
        pytest.param(EffectPhase.ON_END, id="on_end"),
        pytest.param(EffectPhase.ON_DECISION, id="on_decision"),
        pytest.param(EffectPhase.DEFAULT, id="default"),
    ],
)
def test_other_phases_neither_damage_nor_count(session, host, phase):
    status = gain(session, host)

    result = status.use(session, phase)

    assert not result.success
    assert host.current_hp == MAX_HP
    assert status.nr_round == 0
    play_round(session, status)
    assert host.current_hp == MAX_HP - DOSE


def test_fainted_host_takes_no_damage(session, host):
    status = gain(session, host)
    host.is_fainted = True
    host.current_hp = 0

    result = play_round(session, status)

    assert not result.success
    assert host.current_hp == 0
