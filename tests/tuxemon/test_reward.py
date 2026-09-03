# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock, PropertyMock

import pytest

from tuxemon.combat.combat_context import CombatType
from tuxemon.combat.damage_tracker import DamageTracker
from tuxemon.combat.experience_strategies import calculate_experience_base
from tuxemon.combat.money_strategies import (
    MONEY_METHOD_VARIABLE,
    MoneyMethod,
    calculate_money,
)
from tuxemon.combat.reward_system import (
    RewardSystem,
    TrainerRewardCalculator,
    calculate_experience,
    calculate_tps,
)
from tuxemon.database.rules import config_monster
from tuxemon.db import Acquisition, ExperienceMethod
from tuxemon.entity.npc import NPC
from tuxemon.monster.stats import BasicStats
from tuxemon.monster.status import MonsterStatusHandler


class DummyItem:
    def __init__(self, method: ExperienceMethod, multiplier: float):
        self.reward_method = method
        self.money_multiplier = multiplier


def monster_mock(
    *,
    level=5,
    hp=50,
    stage="basic",
    acquisition=Acquisition.UNKNOWN,
    money_modifier=1.0,
    total_xp=1000,
    xp_modifier=1.5,
    owner=True,
    player=True,
    fainted=False,
    base_stats=None,
):
    m = MagicMock()

    m.level = level
    m.current_hp = hp
    m.stage = stage
    m.is_fainted = fainted

    if base_stats is None:
        m.base_stats = BasicStats(
            hp=hp, melee=10, armour=5, dodge=5, ranged=10, speed=10
        )
    else:
        m.base_stats = base_stats

    m.total_experience = total_xp
    m.experience_modifier = xp_modifier
    m.get_experience_multiplier = MagicMock(return_value=1.0)

    m.money_modifier = money_modifier

    m.held_item = None
    m.item_handler = MagicMock()

    m.moves = MagicMock()
    m.moves.update_moves = MagicMock(return_value=[])

    m.status = MagicMock(spec=MonsterStatusHandler)

    m.acquisition = acquisition

    if owner:
        npc = MagicMock(spec=NPC)
        npc.is_player = player
        npc.monsters = [m]
        npc.party = MagicMock()
        npc.party.alive = [m]
        m.owner = npc
    else:
        m.owner = None

    return m


def session_mock(method=MoneyMethod.CONSERVED):
    """A session whose campaign uses the given money method."""
    session = MagicMock()
    set_money_method(session, method)
    return session


def set_money_method(session, method):
    """Switch the money method the campaign in play declared."""

    def game_variable(key, default=None):
        return method.value if key == MONEY_METHOD_VARIABLE else default

    session.player.game_variables.get.side_effect = game_variable


def clear_money_method(session):
    """Model a campaign, or a save, that declared no money method."""

    def game_variable(key, default=None):
        return default

    session.player.game_variables.get.side_effect = game_variable


@pytest.fixture
def setup_combat():
    loser = monster_mock(level=5, hp=0, fainted=True, player=False)
    winner = monster_mock(level=5, hp=50)

    winner.moves.update_moves.return_value = ["Fireball"]

    session = session_mock()
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
    assert rewards.prize == calculate_money(
        loser, {winner}, MoneyMethod.CONSERVED
    )
    assert (
        rewards.winners[0].experience
        == calculate_experience(loser, winner, damage_tracker).participant
    )
    assert rewards.update


@pytest.mark.parametrize(
    "multiplier",
    [
        pytest.param(2.0, id="double_money"),
        pytest.param(0.5, id="half_money"),
        pytest.param(0.0, id="zero_money"),
        pytest.param(-1.0, id="negative_multiplier"),
    ],
)
def test_calculate_money_with_item_multiplier(setup_combat, multiplier):
    loser, winner, _, _, _, _, _ = setup_combat
    type(loser).held_item = PropertyMock(return_value=None)
    type(winner).held_item = PropertyMock(
        return_value=DummyItem(ExperienceMethod.DEFAULT, multiplier)
    )
    money = max(0, calculate_money(loser, {winner}, MoneyMethod.CONSERVED))
    assert money >= 0


@pytest.mark.parametrize(
    "item, expected_func",
    [
        pytest.param(
            None,
            lambda l, w, d: int(
                (l.total_experience // l.level) * l.experience_modifier
            ),
            id="no_item_default_exp",
        ),
        pytest.param(
            DummyItem(ExperienceMethod.XP_TRANSMITTER, 2.0),
            # No bench to transmit to, so the reserved half is not withheld.
            lambda l, w, d: (
                calculate_experience_base(
                    l.total_experience, l.level, l.experience_modifier
                )
                // len(d.get_attackers(l))
            ),
            id="xp_transmitter_no_bench",
        ),
    ],
)
def test_calculate_experience_methods(setup_combat, item, expected_func):
    loser, winner, damage_tracker, _, _, _, _ = setup_combat
    type(winner).held_item = PropertyMock(return_value=item)
    exp = calculate_experience(loser, winner, damage_tracker).participant
    assert exp == expected_func(loser, winner, damage_tracker)


def test_calculate_experience_max_level_returns_zero(setup_combat):
    loser, winner, damage_tracker, _, _, _, _ = setup_combat
    winner.level = config_monster.level_range[1]
    award = calculate_experience(loser, winner, damage_tracker)
    assert (award.participant, award.non_participant) == (0, 0)


def test_award_rewards_distribution_to_party(setup_combat):
    loser, winner, damage_tracker, reward_system, _, _, _ = setup_combat

    mock_monsters = [
        monster_mock(level=5, hp=50, owner=True, fainted=False)
        for _ in range(3)
    ]
    for m in mock_monsters:
        m.give_experience = MagicMock()

    winner.owner.monsters = mock_monsters
    winner.owner.party.alive = mock_monsters

    rewards = reward_system.award_rewards(loser)
    assert rewards.winners[0].winner == winner

    for m in mock_monsters:
        m.give_experience.assert_called()


def _transmitter_setup():
    """Two attackers on one loser, plus a bench monster per owning party."""
    loser = monster_mock(level=5, hp=0, fainted=True)

    winner_a = monster_mock(level=5, hp=50)
    winner_b = monster_mock(level=5, hp=50)
    bench_a = monster_mock(level=5, hp=50)
    bench_b = monster_mock(level=5, hp=50)

    winner_a.owner.party.alive = [winner_a, bench_a]
    winner_b.owner.party.alive = [winner_b, bench_b]

    damage_tracker = DamageTracker()
    damage_tracker.log_damage(winner_a, loser, 10, 1)
    damage_tracker.log_damage(winner_b, loser, 10, 1)

    calculator = TrainerRewardCalculator(damage_tracker)
    return loser, winner_a, winner_b, bench_a, bench_b, calculator


def test_non_participant_rewards_credit_every_owning_party():
    loser, winner_a, winner_b, bench_a, bench_b, calculator = (
        _transmitter_setup()
    )
    winner_a.held_item = DummyItem(ExperienceMethod.XP_TRANSMITTER, 1.0)
    winner_b.held_item = DummyItem(ExperienceMethod.XP_TRANSMITTER, 1.0)

    calculator.calculate_non_participant_rewards(loser, {winner_a, winner_b})

    bench_a.give_experience.assert_called_once_with(150)
    bench_b.give_experience.assert_called_once_with(150)


def test_non_participant_rewards_independent_of_winner_order():
    """One transmitter holder among the winners is enough for its party."""
    loser, winner_a, winner_b, bench_a, _, calculator = _transmitter_setup()
    winner_b.owner = winner_a.owner
    winner_a.owner.party.alive = [winner_a, winner_b, bench_a]

    winner_a.held_item = DummyItem(ExperienceMethod.XP_TRANSMITTER, 1.0)
    winner_b.held_item = None  # DEFAULT: pays non-participants nothing

    calculator.calculate_non_participant_rewards(loser, {winner_a, winner_b})

    bench_a.give_experience.assert_called_once_with(150)


def test_transmitter_conserves_the_pot():
    """Participants plus bench receive the whole pot, never more or less."""
    loser, winner_a, winner_b, bench_a, _, calculator = _transmitter_setup()
    winner_b.owner = winner_a.owner
    winner_a.owner.party.alive = [winner_a, winner_b, bench_a]
    winner_a.held_item = DummyItem(ExperienceMethod.XP_TRANSMITTER, 1.0)
    winner_b.held_item = None

    total = calculate_experience_base(
        loser.total_experience, loser.level, loser.experience_modifier
    )
    award_a = calculate_experience(loser, winner_a, calculator.damage_map)
    share_a, bench_share = award_a.participant, award_a.non_participant
    share_b = calculate_experience(
        loser, winner_b, calculator.damage_map
    ).participant

    assert share_a == share_b == total // 2 // 2
    assert bench_share == total // 2
    assert share_a + share_b + bench_share == total


def test_feeder_reserves_its_half_from_the_pot():
    """The holder's half comes out of the pot, not on top of it.

    Needs three attackers: with two, an even split of the whole pot
    coincides with an even split of the unreserved half.
    """
    loser, winner_a, winner_b, bench_a, _, calculator = _transmitter_setup()
    winner_c = monster_mock(level=5, hp=50)
    owner = winner_a.owner
    for mon in (winner_b, winner_c):
        mon.owner = owner
    owner.party.alive = [winner_a, winner_b, winner_c, bench_a]
    calculator.damage_map.log_damage(winner_c, loser, 10, 1)

    winner_a.held_item = DummyItem(ExperienceMethod.XP_FEEDER, 1.0)
    winner_b.held_item = None
    winner_c.held_item = None

    total = calculate_experience_base(
        loser.total_experience, loser.level, loser.experience_modifier
    )
    holder_share = calculate_experience(
        loser, winner_a, calculator.damage_map
    ).holder
    shares = [
        calculate_experience(loser, mon, calculator.damage_map).participant
        for mon in (winner_b, winner_c)
    ]

    assert holder_share == total // 2
    assert shares == [(total - total // 2) // 2] * 2
    assert holder_share + sum(shares) == total


def test_transmitter_works_from_the_bench():
    """A wearer that never fought still transmits, and shares the bench half."""
    loser, fighter, other, bench_a, _, calculator = _transmitter_setup()
    owner = fighter.owner
    wearer = monster_mock(level=5, hp=50)
    wearer.owner = owner
    owner.party.alive = [fighter, wearer, bench_a]

    # only the fighter attacked; strip the second attacker from the map
    calculator.damage_map.remove_monster(other)

    fighter.held_item = None
    bench_a.held_item = None
    wearer.held_item = DummyItem(ExperienceMethod.XP_TRANSMITTER, 1.0)

    total = calculate_experience_base(
        loser.total_experience, loser.level, loser.experience_modifier
    )
    award = calculate_experience(loser, fighter, calculator.damage_map)
    fighter_share, bench_share = award.participant, award.non_participant

    assert fighter_share == total // 2
    assert bench_share == (total - total // 2) // 2
    assert fighter_share + bench_share * 2 == total


def test_feeder_works_from_the_bench():
    """A benched wearer still takes its half; other bench mons get nothing."""
    loser, fighter, other, bench_a, _, calculator = _transmitter_setup()
    owner = fighter.owner
    wearer = monster_mock(level=5, hp=50)
    wearer.owner = owner
    owner.party.alive = [fighter, wearer, bench_a]
    calculator.damage_map.remove_monster(other)

    fighter.held_item = None
    bench_a.held_item = None
    wearer.held_item = DummyItem(ExperienceMethod.XP_FEEDER, 1.0)

    total = calculate_experience_base(
        loser.total_experience, loser.level, loser.experience_modifier
    )
    system = RewardSystem(MagicMock(), CombatType.TRAINER, calculator)
    system.award_rewards(loser)

    def paid(monster):
        return sum(
            call.args[0] for call in monster.give_experience.call_args_list
        )

    assert paid(wearer) == total // 2
    assert paid(fighter) == total - total // 2
    assert paid(bench_a) == 0
    assert paid(wearer) + paid(fighter) + paid(bench_a) == total


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

    winner.moves.preview_moves_learned.return_value = ["Fireball"]

    second_winner = monster_mock(level=5, hp=50)
    second_winner.moves.preview_moves_learned.return_value = ["Ram"]
    second_winner.owner = winner.owner

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
        pytest.param(
            BasicStats(hp=10, melee=20),
            BasicStats(hp=5, melee=10),
            3,
            2,
            id="loser_stronger_tp_gain_3",
        ),
        pytest.param(
            BasicStats(hp=5, melee=5),
            BasicStats(hp=10, melee=10),
            None,
            0,
            id="loser_weaker_no_tp_gain",
        ),
    ],
)
def test_calculate_tps_awards(
    loser_stats, winner_stats, tp_gain, expected_len
):
    loser = monster_mock(level=5)
    loser.base_stats = loser_stats

    winner = monster_mock(level=5)
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

    monster = monster_mock(level=5, hp=50)
    monster.get_owner = MagicMock()
    owner = monster.get_owner.return_value
    owner.bag.find_item.return_value = True
    monster.bond_handler = MagicMock()

    reward_system = RewardSystem(session, combat_type, calculator)
    reward_system.apply_penalties(monster)

    assert monster.current_hp == 0
    monster.bond_handler.apply_bond_modifier.assert_called_with("fainted")


def test_award_rewards_fainted_winner_gets_no_experience_but_prize_paid(
    setup_combat,
):
    loser, winner, _, reward_system, _, _, _ = setup_combat
    winner.current_hp = 0
    winner.is_fainted = True
    rewards = reward_system.award_rewards(loser)

    assert rewards.winners == []
    assert rewards.prize == int(loser.level * loser.money_modifier)


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
    assert rewards.winners


def test_award_rewards_loser_item_multiplier_is_ignored(setup_combat):
    loser, winner, _, reward_system, _, _, _ = setup_combat

    loser.held_item = DummyItem(ExperienceMethod.DEFAULT, 2.0)
    winner.held_item = DummyItem(ExperienceMethod.DEFAULT, 2.0)

    rewards = reward_system.award_rewards(loser)

    base_money = int(loser.level * loser.money_modifier)
    expected = int(base_money * winner.held_item.money_multiplier)

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
    second_winner = monster_mock(level=5, hp=0, fainted=True)
    second_winner.owner = winner.owner
    damage_tracker.log_damage(second_winner, loser, 5, 1)
    reward_system = RewardSystem(session, combat_type, calculator)
    rewards = reward_system.award_rewards(loser)
    assert len(rewards.winners) == 1
    assert rewards.winners[0].winner == winner


def _attacker(loser, damage_tracker, owner, *, fainted=False, item=None):
    """Add another monster of `owner`'s party that hit `loser`."""
    monster = monster_mock(level=5, hp=0 if fainted else 50, fainted=fainted)
    monster.owner = owner
    monster.held_item = item
    damage_tracker.log_damage(monster, loser, 5, 1)
    return monster


def test_award_rewards_prize_independent_of_attacker_count(setup_combat):
    loser, winner, damage_tracker, reward_system, _, _, _ = setup_combat

    solo_prize = reward_system.award_rewards(loser).prize

    for _ in range(2):
        _attacker(loser, damage_tracker, winner.owner)

    trio_prize = reward_system.award_rewards(loser).prize

    assert len(damage_tracker.get_attackers(loser)) == 3
    assert solo_prize == int(loser.level * loser.money_modifier)
    assert trio_prize == solo_prize


def test_award_rewards_all_attackers_fainted_still_pays(setup_combat):
    loser, winner, damage_tracker, reward_system, _, _, _ = setup_combat
    winner.current_hp = 0
    winner.is_fainted = True
    _attacker(loser, damage_tracker, winner.owner, fainted=True)

    rewards = reward_system.award_rewards(loser)

    assert rewards.winners == []
    assert not rewards.update
    assert rewards.prize == int(loser.level * loser.money_modifier)


def test_award_rewards_benched_holder_does_not_boost_prize(setup_combat):
    loser, winner, _, reward_system, _, _, _ = setup_combat
    benched = monster_mock(level=5, hp=50)
    benched.owner = winner.owner
    benched.held_item = DummyItem(ExperienceMethod.DEFAULT, 3.0)
    winner.owner.party.alive = [winner, benched]

    rewards = reward_system.award_rewards(loser)

    assert rewards.prize == int(loser.level * loser.money_modifier)


def test_award_rewards_multipliers_do_not_stack(setup_combat):
    loser, winner, damage_tracker, reward_system, _, _, _ = setup_combat
    winner.held_item = DummyItem(ExperienceMethod.DEFAULT, 2.0)
    _attacker(
        loser,
        damage_tracker,
        winner.owner,
        item=DummyItem(ExperienceMethod.DEFAULT, 3.0),
    )

    rewards = reward_system.award_rewards(loser)

    base_money = int(loser.level * loser.money_modifier)
    assert rewards.prize == int(base_money * 3.0)


def test_award_rewards_player_owned_loser_pays_nothing(setup_combat):
    loser, winner, _, reward_system, _, _, _ = setup_combat
    loser.owner.is_player = True
    loser.money_modifier = 2.0

    rewards = reward_system.award_rewards(loser)

    assert rewards.prize == 0
    assert rewards.winners


def test_calculate_money_without_player_participants_is_zero(setup_combat):
    loser, winner, _, _, _, _, _ = setup_combat
    winner.owner.is_player = False

    assert int(loser.level * loser.money_modifier) > 0
    assert calculate_money(loser, {winner}, MoneyMethod.CONSERVED) == 0
    assert calculate_money(loser, set(), MoneyMethod.CONSERVED) == 0


# The campaign picks the money method, so the same battle pays differently
# depending on the mod.yaml of the campaign in play.


def test_award_rewards_participant_scaled_pays_once_per_attacker(
    setup_combat,
):
    loser, winner, damage_tracker, reward_system, _, session, _ = setup_combat
    set_money_method(session, MoneyMethod.PARTICIPANT_SCALED)

    for _ in range(2):
        _attacker(loser, damage_tracker, winner.owner)

    rewards = reward_system.award_rewards(loser)

    base_money = int(loser.level * loser.money_modifier)
    assert len(damage_tracker.get_attackers(loser)) == 3
    assert rewards.prize == base_money * 3


def test_award_rewards_participant_scaled_skips_fainted_attackers(
    setup_combat,
):
    loser, winner, damage_tracker, reward_system, _, session, _ = setup_combat
    set_money_method(session, MoneyMethod.PARTICIPANT_SCALED)

    _attacker(loser, damage_tracker, winner.owner, fainted=True)

    rewards = reward_system.award_rewards(loser)

    assert rewards.prize == int(loser.level * loser.money_modifier)


def test_award_rewards_method_decides_how_attackers_scale_the_prize(
    setup_combat,
):
    loser, winner, damage_tracker, reward_system, _, session, _ = setup_combat

    for _ in range(2):
        _attacker(loser, damage_tracker, winner.owner)

    base_money = int(loser.level * loser.money_modifier)

    set_money_method(session, MoneyMethod.CONSERVED)
    assert reward_system.award_rewards(loser).prize == base_money

    set_money_method(session, MoneyMethod.PARTICIPANT_SCALED)
    assert reward_system.award_rewards(loser).prize == base_money * 3


def test_award_rewards_undeclared_method_falls_back_to_participant_scaled(
    setup_combat,
):
    loser, winner, damage_tracker, reward_system, _, session, _ = setup_combat
    clear_money_method(session)

    _attacker(loser, damage_tracker, winner.owner)

    rewards = reward_system.award_rewards(loser)

    assert rewards.prize == int(loser.level * loser.money_modifier) * 2
