# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock, PropertyMock

import pytest

from tuxemon.combat.combat_context import CombatType
from tuxemon.combat.damage_tracker import DamageTracker
from tuxemon.combat.experience_strategies import calculate_experience_base
from tuxemon.combat.reward_system import (
    RewardSystem,
    TrainerRewardCalculator,
    calculate_experience,
    calculate_money,
    calculate_tps,
)
from tuxemon.db import Acquisition, ExperienceMethod
from tuxemon.monster import Monster
from tuxemon.monster_dir.stats import BasicStats
from tuxemon.monster_dir.status import MonsterStatusHandler
from tuxemon.npc import NPC
from tuxemon.prepare import MAX_LEVEL


class DummyItem:
    def __init__(self, method: ExperienceMethod, multiplier: float):
        self.reward_method = method
        self.money_multiplier = multiplier


@pytest.fixture
def setup_combat():
    loser = Monster()
    loser.name = "pairagrin"
    loser.set_level(5)
    loser.money_modifier = 1.0
    loser.status = MagicMock(spec=MonsterStatusHandler)
    loser.current_hp = 0
    loser.stage = "basic"
    loser.moves = MagicMock()
    loser.set_total_experience(1000)
    loser.set_experience_modifier(1.5)

    winner = Monster()
    winner.name = "rockitten"
    winner.set_level(5)
    winner.moves = MagicMock()
    winner.current_hp = 50
    winner.stage = "basic"
    winner.acquisition = Acquisition.UNKNOWN
    winner.owner = MagicMock(spec=NPC)
    winner.owner.is_player = True
    winner.owner.monsters = [winner]
    winner.owner.party = MagicMock()
    winner.owner.party.alive = [winner]
    winner.base_stats = BasicStats()

    session = MagicMock()
    combat_type = CombatType.TRAINER

    damage_tracker = DamageTracker()
    damage_tracker.log_damage(winner, loser, 10, 1)

    calculator = TrainerRewardCalculator(damage_tracker)
    reward_system = RewardSystem(session, combat_type, calculator)

    return (
        loser,
        winner,
        damage_tracker,
        reward_system,
        calculator,
        session,
        combat_type,
    )


def test_reward_system_basic(setup_combat):
    loser, winner, damage_tracker, reward_system, _, _, _ = setup_combat
    rewards = reward_system.award_rewards(loser)

    assert len(rewards.winners) == 1
    assert rewards.winners[0].winner == winner
    assert rewards.winners[0].money == calculate_money(loser, winner)
    assert rewards.prize == calculate_money(loser, winner)
    assert (
        rewards.winners[0].experience
        == calculate_experience(loser, winner, damage_tracker)[0]
    )
    assert rewards.update


@pytest.mark.parametrize("multiplier", [2.0, 0.5, 0.0, -1.0])
def test_calculate_money_with_item_multiplier(setup_combat, multiplier):
    loser, winner, _, _, _, _, _ = setup_combat
    type(loser).held_item = PropertyMock(return_value=None)
    type(winner).held_item = PropertyMock(
        return_value=DummyItem(ExperienceMethod.DEFAULT, multiplier)
    )
    money = calculate_money(loser, winner)
    assert money >= 0


@pytest.mark.parametrize(
    "item,expected_func",
    [
        (
            None,
            lambda l, w, d: int(
                (l.total_experience // l.level) * l.experience_modifier
            ),
        ),
        (
            DummyItem(ExperienceMethod.XP_TRANSMITTER, 2.0),
            lambda l, w, d: calculate_experience_base(
                l.total_experience, l.level, l.experience_modifier
            )
            // 2
            // len(d.get_attackers(l)),
        ),
    ],
)
def test_calculate_experience_methods(setup_combat, item, expected_func):
    loser, winner, damage_tracker, _, _, _, _ = setup_combat
    type(winner).held_item = PropertyMock(return_value=item)
    exp, _ = calculate_experience(loser, winner, damage_tracker)
    assert exp == expected_func(loser, winner, damage_tracker)


def test_calculate_experience_max_level_returns_zero(setup_combat):
    loser, winner, damage_tracker, _, _, _, _ = setup_combat
    winner.set_level(MAX_LEVEL)
    exp = calculate_experience(loser, winner, damage_tracker)
    assert exp == (0, 0)


def test_award_rewards_distribution_to_party(setup_combat):
    loser, winner, damage_tracker, reward_system, _, _, _ = setup_combat
    mock_monsters = [
        MagicMock(
            spec=Monster,
            give_experience=MagicMock(),
            moves=MagicMock(),
            level=5,
            status=MonsterStatusHandler(),
            current_hp=50,
            is_fainted=False,
            stage="basic",
        )
        for _ in range(3)
    ]
    winner.owner.monsters = mock_monsters
    winner.owner.party.alive = mock_monsters

    rewards = reward_system.award_rewards(loser)
    assert rewards.winners[0].winner == winner
    for monster in mock_monsters:
        monster.give_experience.assert_called()


def test_award_rewards_no_winners(setup_combat):
    loser, _, _, _, _, session, combat_type = setup_combat
    empty_tracker = DamageTracker()
    calculator = TrainerRewardCalculator(empty_tracker)
    reward_system = RewardSystem(session, combat_type, calculator)
    rewards = reward_system.award_rewards(loser)
    assert rewards.winners == []
    assert rewards.prize == 0
    assert not rewards.update
    assert rewards.moves == []
    assert rewards.messages == []


def test_award_rewards_moves_updates(setup_combat):
    (
        loser,
        winner,
        damage_tracker,
        reward_system,
        calculator,
        session,
        combat_type,
    ) = setup_combat
    winner.moves.update_moves.return_value = ["Fireball"]

    second_winner = Monster()
    second_winner.name = "rockitten"
    second_winner.stage = "basic"
    second_winner.set_level(5)
    second_winner.moves = MagicMock()
    second_winner.moves.update_moves.return_value = ["Ram"]
    second_winner.acquisition = Acquisition.UNKNOWN
    second_winner.owner = winner.owner
    second_winner.current_hp = 50
    second_winner.item_handler = MagicMock(held_item=MagicMock(slug="default"))

    damage_tracker.log_damage(second_winner, loser, 5, 1)

    reward_system = RewardSystem(session, combat_type, calculator)
    rewards = reward_system.award_rewards(loser)
    assert set(rewards.moves) == {"Fireball", "Ram"}


def test_award_rewards_non_player_monster(setup_combat):
    loser, winner, _, reward_system, _, _, _ = setup_combat
    winner.owner.is_player = False
    rewards = reward_system.award_rewards(loser)
    assert rewards.prize == 0
    assert rewards.messages == []
    assert not rewards.update


@pytest.mark.parametrize(
    "loser_stats,winner_stats,tp_gain,expected_len",
    [
        (BasicStats(hp=10, melee=20), BasicStats(hp=5, melee=10), 3, 2),
        (BasicStats(hp=5, melee=5), BasicStats(hp=10, melee=10), None, 0),
    ],
)
def test_calculate_tps_awards(
    loser_stats, winner_stats, tp_gain, expected_len
):
    loser = Monster()
    loser.base_stats = loser_stats
    winner = Monster()
    winner.base_stats = winner_stats
    winner.give_tps = MagicMock()
    awarded = (
        calculate_tps(winner, loser, tp_gain=tp_gain)
        if tp_gain
        else calculate_tps(winner, loser)
    )
    assert len(awarded) == expected_len
    if expected_len:
        for stat, gain in awarded:
            winner.give_tps.assert_any_call(stat, gain)
    else:
        winner.give_tps.assert_not_called()


def test_apply_penalties_sets_hp_and_bond(setup_combat):
    _, _, _, _, calculator, session, combat_type = setup_combat
    monster = Monster()
    monster.current_hp = 50
    monster.get_owner = MagicMock()
    owner = monster.get_owner.return_value
    owner.bag.find_item.return_value = True
    monster.bond_handler = MagicMock()

    reward_system = RewardSystem(session, combat_type, calculator)
    reward_system.apply_penalties(monster)
    assert monster.current_hp == 0
    monster.bond_handler.apply_bond_modifier.assert_called_with("fainted")


def test_award_rewards_fainted_winner_gets_none(setup_combat):
    loser, winner, _, reward_system, _, _, _ = setup_combat
    winner.current_hp = 0
    rewards = reward_system.award_rewards(loser)
    assert rewards.winners == []
    assert rewards.prize == 0


def test_award_rewards_winner_without_owner(setup_combat):
    loser, winner, _, reward_system, _, _, _ = setup_combat
    winner.owner = None
    rewards = reward_system.award_rewards(loser)
    assert rewards.winners == []
    assert rewards.prize == 0


def test_award_rewards_loser_with_zero_money_modifier(setup_combat):
    loser, winner, _, reward_system, _, _, _ = setup_combat
    loser.money_modifier = 0
    rewards = reward_system.award_rewards(loser)
    assert rewards.prize == 0
    assert all(entry.money == 0 for entry in rewards.winners)


def test_award_rewards_loser_with_item_multiplier(setup_combat):
    loser, winner, _, reward_system, _, _, _ = setup_combat
    type(loser).held_item = PropertyMock(
        return_value=DummyItem(ExperienceMethod.DEFAULT, 2.0)
    )
    type(winner).held_item = PropertyMock(
        return_value=DummyItem(ExperienceMethod.DEFAULT, 2.0)
    )
    rewards = reward_system.award_rewards(loser)
    base_money = int(loser.level * loser.money_modifier)
    expected = (
        base_money
        * loser.held_item.money_multiplier
        * winner.held_item.money_multiplier
    )
    assert rewards.prize == expected


def test_award_rewards_multiple_winners_mixed_states(setup_combat):
    (
        loser,
        winner,
        damage_tracker,
        reward_system,
        calculator,
        session,
        combat_type,
    ) = setup_combat
    second_winner = Monster()
    second_winner.name = "ally"
    second_winner.stage = "basic"
    second_winner.set_level(5)
    second_winner.moves = MagicMock()
    second_winner.acquisition = Acquisition.UNKNOWN
    second_winner.owner = winner.owner
    second_winner.current_hp = 0
    damage_tracker.log_damage(second_winner, loser, 5, 1)

    reward_system = RewardSystem(session, combat_type, calculator)
    rewards = reward_system.award_rewards(loser)
    assert len(rewards.winners) == 1
    assert rewards.winners[0].winner == winner
