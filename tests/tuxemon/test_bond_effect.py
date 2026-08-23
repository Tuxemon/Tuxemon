# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from tuxemon.core.effects.bond import BondEffect
from tuxemon.database.rules import config_monster
from tuxemon.db import EvolutionStage
from tuxemon.monster.bond import BondHandler


@pytest.fixture(autouse=True)
def no_milestones(monkeypatch):
    monkeypatch.setattr(config_monster, "bond_milestones", [])


@pytest.fixture
def item():
    mock = MagicMock()
    mock.name = "Heart Biscuit"
    return mock


def target_with_bond(bond, stage=EvolutionStage.BASIC):
    target = MagicMock()
    target.bond_handler = BondHandler()
    target.bond_handler.bond = bond
    target.stage = stage
    return target


@pytest.mark.parametrize(
    "taste_warm,taste_cold",
    [
        pytest.param("salty", "sweet", id="salty_sweet"),
        pytest.param("hearty", "flakey", id="hearty_flakey"),
        pytest.param("refined", "mild", id="refined_mild"),
    ],
)
def test_bond_gain_ignores_tastes(item, taste_warm, taste_cold):
    target = target_with_bond(50)
    target.taste_warm = taste_warm
    target.taste_cold = taste_cold

    result = BondEffect(amount=5).apply_item_target(MagicMock(), item, target)

    assert result.success is True
    assert target.bond_handler.bond == 55


def test_bond_accepts_a_negative_amount(item):
    target = target_with_bond(50)

    BondEffect(amount=-5).apply_item_target(MagicMock(), item, target)

    assert target.bond_handler.bond == 45


def test_bond_treats_a_float_as_a_fraction(item):
    target = target_with_bond(50)

    BondEffect(amount=0.5).apply_item_target(MagicMock(), item, target)

    assert target.bond_handler.bond == 75


def test_bond_stops_at_the_stage_floor(item, monkeypatch):
    monkeypatch.setattr(
        config_monster, "bond_stage_floors", {"stage2": 40}, raising=False
    )
    target = target_with_bond(45, stage=EvolutionStage.STAGE2)

    BondEffect(amount=-20).apply_item_target(MagicMock(), item, target)

    assert target.bond_handler.bond == 40


def test_bond_fails_when_bond_cannot_move(item):
    target = target_with_bond(BondHandler.MAX_BOND)

    result = BondEffect(amount=5).apply_item_target(MagicMock(), item, target)

    assert result.success is False
    assert target.bond_handler.bond == BondHandler.MAX_BOND
