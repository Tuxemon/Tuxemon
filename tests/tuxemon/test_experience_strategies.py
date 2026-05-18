# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock

import pytest

from tuxemon.combat.damage_tracker import DamageTracker
from tuxemon.combat.experience_strategies import (
    BondExperienceStrategy,
    DamageProportionalExperienceStrategy,
    DefaultExperienceStrategy,
    EqualExperienceStrategy,
    FeederExperienceStrategy,
    OverkillExperienceStrategy,
    StageScalingExperienceStrategy,
    SurvivorExperienceStrategy,
    TransmitterExperienceStrategy,
    calculate_experience,
    calculate_experience_base,
)
from tuxemon.database.rules import config_monster
from tuxemon.db import EvolutionStage, ExperienceMethod


class DummyMonster:
    def __init__(self, name="dummy", level=5, total_exp=1000, exp_mod=1.0):
        self.name = name
        self.level = level
        self.total_experience = total_exp
        self.experience_modifier = exp_mod
        self.held_item = None
        self.owner = None
        self.current_hp = 10

    def get_experience_multiplier(self):
        return 1.0

    @property
    def is_fainted(self):
        return self.current_hp <= 0


@pytest.fixture
def setup_combat():
    loser = DummyMonster("loser", level=5, total_exp=1000, exp_mod=1.5)
    winner = DummyMonster("winner", level=5, total_exp=1000, exp_mod=1.0)
    second_attacker = DummyMonster(
        "ally", level=5, total_exp=1000, exp_mod=1.0
    )

    damages = DamageTracker()
    damages.log_damage(winner, loser, 10, 1)
    damages.log_damage(winner, loser, 5, 2)
    damages.log_damage(second_attacker, loser, 20, 3)

    return loser, winner, second_attacker, damages


@pytest.mark.parametrize(
    "strategy_cls",
    [
        pytest.param(DefaultExperienceStrategy, id="default"),
        pytest.param(EqualExperienceStrategy, id="equal"),
        pytest.param(OverkillExperienceStrategy, id="overkill"),
        pytest.param(
            DamageProportionalExperienceStrategy, id="damage_proportional"
        ),
    ],
)
def test_basic_strategies(strategy_cls, setup_combat):
    loser, winner, _, damages = setup_combat
    strat = strategy_cls()
    exp, non = strat.calculate(loser, winner, damages, 1.0)
    assert exp > 0
    assert non == 0


def test_feeder_strategy_with_item(setup_combat):
    loser, winner, _, damages = setup_combat
    winner.held_item = MagicMock()
    winner.held_item.reward_method = ExperienceMethod.XP_FEEDER
    strat = FeederExperienceStrategy()
    exp, non = strat.calculate(loser, winner, damages, 1.0)
    assert exp >= 0
    assert non == 0


def test_transmitter_strategy_with_owner(setup_combat):
    loser, winner, _, damages = setup_combat
    owner = MagicMock()
    owner.party.alive = [winner]
    winner.owner = owner
    strat = TransmitterExperienceStrategy()
    exp, non = strat.calculate(loser, winner, damages, 1.0)
    assert exp >= 0
    assert non >= 0


def test_calculate_experience_default(setup_combat):
    loser, winner, _, damages = setup_combat
    winner.held_item = None
    exp, non = calculate_experience(loser, winner, damages)
    assert exp > 0
    assert non == 0


def test_calculate_experience_max_level(setup_combat):
    loser, winner, _, damages = setup_combat
    winner.level = config_monster.level_range[1]
    exp, non = calculate_experience(loser, winner, damages)
    assert (exp, non) == (0, 0)


def test_calculate_experience_base():
    base = calculate_experience_base(1000, 5, 1.5)
    expected = int((1000 // 5) * 1.5)
    assert base == expected


def test_equal_strategy_multi_attacker(setup_combat):
    loser, winner, ally, damages = setup_combat
    strat = EqualExperienceStrategy()
    exp_winner, _ = strat.calculate(loser, winner, damages, 1.0)
    exp_ally, _ = strat.calculate(loser, ally, damages, 1.0)
    assert exp_winner > exp_ally


def test_damage_proportional_strategy_multi_attacker(setup_combat):
    loser, winner, ally, damages = setup_combat
    strat = DamageProportionalExperienceStrategy()
    exp_winner, _ = strat.calculate(loser, winner, damages, 1.0)
    exp_ally, _ = strat.calculate(loser, ally, damages, 1.0)
    assert exp_ally > exp_winner


def test_transmitter_strategy_with_non_participant(setup_combat):
    loser, winner, ally, damages = setup_combat
    non_participant = DummyMonster(
        "bench", level=5, total_exp=1000, exp_mod=1.0
    )
    owner = MagicMock()
    owner.party.alive = [winner, ally, non_participant]
    winner.owner = owner
    strat = TransmitterExperienceStrategy()
    exp, non = strat.calculate(loser, winner, damages, 1.0)
    assert exp > 0
    assert non > 0


def test_overkill_strategy_final_blow_multi_attacker(setup_combat):
    loser, winner, ally, damages = setup_combat
    strat = OverkillExperienceStrategy()
    exp_winner, _ = strat.calculate(loser, winner, damages, 1.0)
    exp_ally, _ = strat.calculate(loser, ally, damages, 1.0)
    assert exp_ally > exp_winner


def test_feeder_strategy_multi_attacker_item_holder(setup_combat):
    loser, winner, ally, damages = setup_combat
    winner.held_item = MagicMock()
    winner.held_item.reward_method = ExperienceMethod.XP_FEEDER
    ally.held_item = None
    strat = FeederExperienceStrategy()
    exp_winner, _ = strat.calculate(loser, winner, damages, 1.0)
    exp_ally, _ = strat.calculate(loser, ally, damages, 1.0)
    assert exp_winner >= exp_ally


def test_feeder_strategy_multi_attacker_no_item(setup_combat):
    loser, winner, ally, damages = setup_combat
    winner.held_item = None
    ally.held_item = None
    strat = FeederExperienceStrategy()
    exp_winner, _ = strat.calculate(loser, winner, damages, 1.0)
    exp_ally, _ = strat.calculate(loser, ally, damages, 1.0)
    assert exp_winner > 0
    assert exp_ally > 0


def test_bond_experience_strategy(setup_combat):
    loser, winner, _, damages = setup_combat
    winner.bond_handler = MagicMock(bond=50)
    strat = BondExperienceStrategy()
    exp, non = strat.calculate(loser, winner, damages, 1.0)
    assert exp > 0
    assert non == 0


def test_bond_experience_strategy_scaling(setup_combat):
    loser, winner, _, damages = setup_combat
    winner.bond_handler = MagicMock(bond=100)
    strat = BondExperienceStrategy()
    exp_high, _ = strat.calculate(loser, winner, damages, 1.0)
    winner.bond_handler.bond = 1
    exp_low, _ = strat.calculate(loser, winner, damages, 1.0)
    assert exp_high > exp_low


def test_stage_scaling_experience_strategy(setup_combat):
    loser, winner, _, damages = setup_combat
    loser.stage = EvolutionStage.STAGE1
    strat = StageScalingExperienceStrategy()
    exp_evolved, _ = strat.calculate(loser, winner, damages, 1.0)

    loser.stage = EvolutionStage.BASIC
    exp_basic, _ = strat.calculate(loser, winner, damages, 1.0)

    assert exp_evolved > exp_basic


def test_survivor_experience_strategy(setup_combat):
    loser, winner, _, damages = setup_combat
    ally = DummyMonster("ally", level=5, total_exp=1000, exp_mod=1.0)
    owner = MagicMock()
    owner.party.alive = [winner, ally]
    winner.owner = owner

    ally.current_hp = 0
    winner.current_hp = 10

    strat = SurvivorExperienceStrategy()
    exp, non = strat.calculate(loser, winner, damages, 1.0)
    assert exp > 0
    assert non == 0
