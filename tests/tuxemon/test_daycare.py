# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from tuxemon.entity.daycare import Daycare
from tuxemon.monster.stats import IndividualValues


def make_monster(
    gender: str = "female",
    level: int = 20,
    evolution_rank: int = 2,
    slug: str = "rockitten",
    name: str = "Rockitten",
    taste_warm: str = "mild",
    taste_cold: str = "sour",
    base_stats_sum: int = 300,
    hp_ratio: float = 0.8,
    history: list | None = None,
    moves: list | None = None,
) -> MagicMock:
    m = MagicMock()
    m.gender = gender
    m.level = level
    m.slug = slug
    m.name = name
    m.taste_warm = taste_warm
    m.taste_cold = taste_cold
    m.hp_ratio = hp_ratio
    m.history = history or []
    m.is_female = gender == "female"
    m.is_male = gender == "male"
    m.evolution_rank.return_value = evolution_rank
    m.moves.get_moves.return_value = moves or []
    m.instance_id = f"iid_{name}_{gender}"
    m.individual_values = IndividualValues()

    base_stats_mock = MagicMock()
    base_stats_mock.sum.return_value = base_stats_sum
    m.base_stats = base_stats_mock

    return m


class FakeOwner:
    def __init__(self, steps: float = 0.0, money: int = 9999):
        self.steps = steps
        self.party = MagicMock()
        self.party.monsters = []
        self.session = MagicMock()

        self.money_controller = MagicMock()
        self.money_controller.money_manager.get_money.return_value = money

        self.game_variables = MagicMock()


def make_owner(steps: float = 0.0, money: int = 9999) -> FakeOwner:
    return FakeOwner(steps=steps, money=money)


def make_session() -> MagicMock:
    session = MagicMock()
    return session


def make_daycare(owner: FakeOwner | None = None) -> Daycare:
    if owner is None:
        owner = make_owner()
    with patch("tuxemon.entity.daycare.get_event_bus"):
        return Daycare(owner)


@pytest.fixture
def owner():
    return make_owner()


@pytest.fixture
def mock_event_bus():
    bus = MagicMock()
    with patch("tuxemon.entity.daycare.get_event_bus", return_value=bus):
        yield bus


@pytest.fixture
def daycare(owner, mock_event_bus):
    return Daycare(owner)


@pytest.fixture
def mother():
    return make_monster(gender="female", name="Mom")


@pytest.fixture
def father():
    return make_monster(gender="male", name="Dad")


class TestAddParent:
    @pytest.mark.parametrize(
        "rank",
        [
            pytest.param(0, id="rank_0_accepted"),
            pytest.param(1, id="rank_1_accepted"),
            pytest.param(2, id="rank_2_accepted"),
            pytest.param(3, id="rank_3_accepted"),
        ],
    )
    def test_any_rank_accepted_for_training(self, daycare, rank):
        m = make_monster(evolution_rank=rank)
        assert daycare.add_parent(m) is True

    def test_first_slot_accepted(self, daycare, mother):
        assert daycare.add_parent(mother) is True
        assert len(daycare.parents) == 1

    def test_second_slot_accepted(self, daycare, mother, father):
        daycare.add_parent(mother)
        assert daycare.add_parent(father) is True
        assert len(daycare.parents) == 2

    def test_third_slot_rejected(self, daycare, mother, father):
        daycare.add_parent(mother)
        daycare.add_parent(father)
        extra = make_monster(gender="female", name="Extra")
        assert daycare.add_parent(extra) is False
        assert len(daycare.parents) == 2

    def test_monster_removed_from_party(self, daycare, mother):
        daycare.owner.party.monsters = [mother]
        daycare.add_parent(mother)
        daycare.owner.party.remove_monster.assert_called_once_with(mother)

    def test_monster_not_in_party_no_remove_called(self, daycare, mother):
        daycare.owner.party.monsters = []
        daycare.add_parent(mother)
        daycare.owner.party.remove_monster.assert_not_called()

    def test_training_steps_start_reset_on_first(self, daycare, mother):
        daycare.owner.steps = 500.0
        daycare.add_parent(mother)
        assert daycare.training_steps_start == 500.0

    def test_training_steps_start_reset_on_second(
        self, daycare, mother, father
    ):
        daycare.owner.steps = 100.0
        daycare.add_parent(mother)
        daycare.owner.steps = 300.0
        daycare.add_parent(father)
        assert daycare.training_steps_start == 300.0

    def test_breeding_flags_reset_on_first(self, daycare, mother):
        daycare.halfway_notified = True
        daycare.ready_notified = True
        daycare.add_parent(mother)
        assert daycare.halfway_notified is False
        assert daycare.ready_notified is False

    def test_breeding_flags_not_reset_on_second(self, daycare, mother, father):
        daycare.add_parent(mother)
        daycare.halfway_notified = True
        daycare.ready_notified = True
        daycare.add_parent(father)
        assert daycare.halfway_notified is True
        assert daycare.ready_notified is True

    def test_same_gender_pair_still_accepted(self, daycare):
        m1 = make_monster(gender="male", name="A")
        m2 = make_monster(gender="male", name="B")
        daycare.add_parent(m1)
        assert daycare.add_parent(m2) is True


class TestWithdrawParents:
    def test_empty_daycare_returns_empty(self, daycare):
        assert daycare.withdraw_parents() == []

    def test_returns_monsters(self, daycare, mother):
        daycare.add_parent(mother)
        result = daycare.withdraw_parents()
        assert mother in result

    def test_parents_cleared_after_withdraw(self, daycare, mother):
        daycare.add_parent(mother)
        daycare.withdraw_parents()
        assert daycare.parents == []

    def test_monsters_added_back_to_party(self, daycare, mother):
        daycare.add_parent(mother)
        daycare.withdraw_parents()
        daycare.owner.party.add_monster.assert_called_with(mother)

    def test_withdraw_does_not_apply_training_exp_anymore(
        self, daycare, mother
    ):
        daycare.add_parent(mother)
        daycare.withdraw_parents()
        mother.give_experience.assert_not_called()

    def test_withdraw_does_not_deduct_money_anymore(self, daycare, mother):
        daycare.add_parent(mother)
        daycare.withdraw_parents()
        daycare.owner.money_controller.money_manager.remove_money.assert_not_called()

    def test_withdraw_does_not_fail_on_insufficient_funds(self, owner):
        owner.money_controller.money_manager.get_money.return_value = 0
        dc = Daycare(owner)
        m = make_monster()
        dc.add_parent(m)
        result = dc.withdraw_parents()
        assert result == [m]

    def test_withdraw_does_not_set_game_variables_anymore(
        self, daycare, mother
    ):
        daycare.add_parent(mother)
        daycare.withdraw_parents()
        daycare.owner.game_variables.set.assert_not_called()

    def test_stale_training_start_is_irrelevant_now(self, owner):
        dc = Daycare(owner)
        dc.training_steps_start = 0
        m = make_monster()
        dc.parents.append(m)
        dc.withdraw_parents()
        m.give_experience.assert_not_called()


class TestCompatible:
    @pytest.mark.parametrize(
        "rank",
        [
            pytest.param(0, id="rank_0"),
            pytest.param(1, id="rank_1"),
            pytest.param(2, id="rank_2"),
            pytest.param(3, id="rank_3"),
        ],
    )
    def test_any_rank_compatible(self, daycare, rank):
        m = make_monster(evolution_rank=rank)
        assert daycare._compatible(m) is True


class TestGenderPairOk:
    @pytest.mark.parametrize(
        "g1,g2,expected",
        [
            pytest.param("female", "male", True, id="female_male"),
            pytest.param("male", "female", True, id="male_female"),
            pytest.param("male", "male", False, id="male_male"),
            pytest.param("female", "female", False, id="female_female"),
            pytest.param("none", "male", False, id="genderless_male"),
            pytest.param("female", "none", False, id="female_genderless"),
            pytest.param("none", "none", False, id="both_genderless"),
        ],
    )
    def test_gender_pair(self, daycare, g1, g2, expected):
        a = make_monster(gender=g1)
        b = make_monster(gender=g2)
        assert daycare._gender_pair_ok(a, b) == expected

    def test_unevolved_pair_cannot_breed(self, daycare):
        a = make_monster(gender="female", evolution_rank=1)
        b = make_monster(gender="male", evolution_rank=1)
        assert daycare._gender_pair_ok(a, b) is False

    def test_one_unevolved_cannot_breed(self, daycare):
        a = make_monster(gender="female", evolution_rank=2)
        b = make_monster(gender="male", evolution_rank=1)
        assert daycare._gender_pair_ok(a, b) is False

    def test_both_evolved_can_breed(self, daycare):
        a = make_monster(gender="female", evolution_rank=2)
        b = make_monster(gender="male", evolution_rank=2)
        assert daycare._gender_pair_ok(a, b) is True


class TestOnSteps:
    def test_training_exp_applied_during_steps(self, daycare, mother):
        daycare.training_exp_rate = 0.25
        daycare.add_parent(mother)

        daycare.on_steps(1000)

        mother.give_experience.assert_called_once_with(250)

    def test_training_cost_deducted_during_steps(self, daycare, mother):
        daycare.training_exp_rate = 1.0
        daycare.training_cost_rate = 1.0
        daycare.add_parent(mother)

        daycare.on_steps(500)

        daycare.owner.money_controller.money_manager.remove_money.assert_called_once_with(
            500
        )

    def test_training_game_variables_set_during_steps(self, daycare, mother):
        daycare.training_exp_rate = 1.0
        daycare.training_cost_rate = 1.0
        daycare.add_parent(mother)

        daycare.on_steps(100)

        daycare.owner.game_variables.set.assert_any_call("daycare_exp", 100)
        daycare.owner.game_variables.set.assert_any_call("daycare_cost", 100)

    def test_training_no_exp_when_zero_steps(self, daycare, mother):
        daycare.add_parent(mother)
        daycare.on_steps(0)
        mother.give_experience.assert_not_called()

    def test_training_no_cost_when_zero_exp(self, daycare, mother):
        daycare.add_parent(mother)
        daycare.on_steps(0)
        daycare.owner.money_controller.money_manager.remove_money.assert_not_called()

    def test_training_insufficient_funds_blocks_exp(self, owner):
        owner.money_controller.money_manager.get_money.return_value = 0
        dc = Daycare(owner)
        dc.training_exp_rate = 1.0
        m = make_monster()
        dc.add_parent(m)

        dc.on_steps(500)

        m.give_experience.assert_not_called()
        owner.money_controller.money_manager.remove_money.assert_not_called()

    def test_training_insufficient_funds_does_not_remove_parent(self, owner):
        owner.money_controller.money_manager.get_money.return_value = 0
        dc = Daycare(owner)
        m = make_monster()
        dc.add_parent(m)

        dc.on_steps(500)

        assert len(dc.parents) == 1

    def test_no_progress_with_one_monster(self, daycare, mother):
        daycare.add_parent(mother)
        daycare.on_steps(5000)
        assert daycare.progress_steps == 0.0

    def test_no_progress_incompatible_pair(self, daycare):
        m1 = make_monster(gender="male", name="A")
        m2 = make_monster(gender="male", name="B")
        daycare.add_parent(m1)
        daycare.add_parent(m2)
        daycare.on_steps(5000)
        assert daycare.progress_steps == 0.0

    def test_progress_accumulates_for_compatible_pair(
        self, daycare, mother, father
    ):
        daycare.add_parent(mother)
        daycare.add_parent(father)
        daycare.on_steps(3000)
        daycare.on_steps(2000)
        assert daycare.progress_steps == 5000.0

    def test_halfway_event_fired(self, daycare, mother, father):
        daycare.add_parent(mother)
        daycare.add_parent(father)
        daycare.on_steps(5000)
        daycare.event_bus.publish.assert_any_call(
            "daycare_halfway", player=daycare.owner
        )

    def test_halfway_event_fired_only_once(self, daycare, mother, father):
        daycare.add_parent(mother)
        daycare.add_parent(father)
        daycare.on_steps(5000)
        daycare.on_steps(1000)
        calls = [
            c
            for c in daycare.event_bus.publish.call_args_list
            if c.args[0] == "daycare_halfway"
        ]
        assert len(calls) == 1

    def test_ready_event_fired(self, daycare, mother, father):
        daycare.add_parent(mother)
        daycare.add_parent(father)
        daycare.on_steps(10000)
        daycare.event_bus.publish.assert_any_call(
            "daycare_ready", player=daycare.owner
        )

    def test_ready_event_fired_only_once(self, daycare, mother, father):
        daycare.add_parent(mother)
        daycare.add_parent(father)
        daycare.on_steps(10000)
        daycare.on_steps(5000)
        calls = [
            c
            for c in daycare.event_bus.publish.call_args_list
            if c.args[0] == "daycare_ready"
        ]
        assert len(calls) == 1

    def test_ready_false_before_threshold(self, daycare, mother, father):
        daycare.add_parent(mother)
        daycare.add_parent(father)
        daycare.on_steps(9999)
        assert daycare.ready() is False

    def test_ready_true_at_threshold(self, daycare, mother, father):
        daycare.add_parent(mother)
        daycare.add_parent(father)
        daycare.on_steps(10000)
        assert daycare.ready() is True

    def test_ready_false_incompatible_pair(self, daycare):
        m1 = make_monster(gender="male", name="A")
        m2 = make_monster(gender="male", name="B")
        daycare.add_parent(m1)
        daycare.add_parent(m2)
        daycare.progress_steps = 99999
        assert daycare.ready() is False


class TestProduceEgg:
    @pytest.fixture
    def mother(self):
        # Higher evolution rank ensures mother is always the seed, so father
        # is always the "other" parent whose moves are inherited.
        return make_monster(gender="female", name="Mom", evolution_rank=3)

    @pytest.fixture(autouse=True)
    def patch_spawn(self):
        self._egg = MagicMock()
        with patch(
            "tuxemon.entity.daycare.Monster.spawn_base", return_value=self._egg
        ):
            yield

    def _ready_daycare(self, owner, mother, father) -> Daycare:
        dc = Daycare(owner)
        dc.add_parent(mother)
        dc.add_parent(father)
        dc.progress_steps = dc.required_steps
        return dc

    def test_raises_if_not_ready(self, daycare, mother):
        daycare.add_parent(mother)
        with pytest.raises(ValueError, match="Breeding not complete"):
            daycare.produce_newborn()

    def test_egg_produced_successfully(self, owner, mother, father):
        owner.session = MagicMock()
        dc = self._ready_daycare(owner, mother, father)
        egg = dc.produce_newborn()
        assert egg is self._egg

    def test_parents_remain_after_newborn(self, owner, mother, father):
        owner.session = MagicMock()
        dc = self._ready_daycare(owner, mother, father)
        dc.produce_newborn()
        assert len(dc.parents) == 2

    def test_parents_not_returned_to_party_after_newborn(
        self, owner, mother, father
    ):
        owner.session = MagicMock()
        dc = self._ready_daycare(owner, mother, father)
        dc.produce_newborn()
        owner.party.add_monster.assert_not_called()

    def test_progress_reset_after_egg(self, owner, mother, father):
        owner.session = MagicMock()
        dc = self._ready_daycare(owner, mother, father)
        dc.produce_newborn()
        assert dc.progress_steps == 0

    def test_egg_acquisition_set_to_bred(self, owner, mother, father):
        owner.session = MagicMock()
        dc = self._ready_daycare(owner, mother, father)
        dc.produce_newborn()
        self._egg.set_acquisition.assert_called_once()

    def test_egg_parents_recorded(self, owner, mother, father):
        owner.session = MagicMock()
        dc = self._ready_daycare(owner, mother, father)
        dc.produce_newborn()
        assert self._egg.mother_iid == mother.instance_id
        assert self._egg.father_iid == father.instance_id

    def test_move_inherited_from_father(self, owner, mother, father):
        owner.session = MagicMock()
        mock_move = MagicMock()
        father.moves.get_moves.return_value = [mock_move]
        dc = self._ready_daycare(owner, mother, father)
        dc.produce_newborn()
        self._egg.moves.add_move.assert_called_once_with(mock_move)

    def test_no_move_inherited_if_father_has_none(self, owner, mother, father):
        owner.session = MagicMock()
        father.moves.get_moves.return_value = []
        dc = self._ready_daycare(owner, mother, father)
        dc.produce_newborn()
        self._egg.moves.add_move.assert_not_called()


class TestDetermineSeed:
    def test_higher_evolution_rank_wins(self, daycare):
        m = make_monster(gender="female", evolution_rank=3, base_stats_sum=100)
        f = make_monster(gender="male", evolution_rank=2, base_stats_sum=200)
        assert daycare._determine_seed(m, f) is m

    def test_higher_base_stats_wins_on_tie_rank(self, daycare):
        m = make_monster(gender="female", evolution_rank=2, base_stats_sum=400)
        f = make_monster(gender="male", evolution_rank=2, base_stats_sum=300)
        assert daycare._determine_seed(m, f) is m

    def test_higher_hp_ratio_wins_on_tie_stats(self, daycare):
        m = make_monster(
            gender="female", evolution_rank=2, base_stats_sum=300, hp_ratio=0.9
        )
        f = make_monster(
            gender="male", evolution_rank=2, base_stats_sum=300, hp_ratio=0.5
        )
        assert daycare._determine_seed(m, f) is m

    def test_random_choice_on_full_tie(self, daycare):
        m = make_monster(
            gender="female", evolution_rank=2, base_stats_sum=300, hp_ratio=0.8
        )
        f = make_monster(
            gender="male", evolution_rank=2, base_stats_sum=300, hp_ratio=0.8
        )
        with patch(
            "tuxemon.entity.daycare.ElementTypesHandler"
        ) as mock_handler:
            mock_handler.calculate_affinity_score.return_value = 1.0
            mock_handler.calculate_resistance_multiplier_for_types.return_value = 1.0
            with patch("random.choice", return_value=m) as mock_choice:
                result = daycare._determine_seed(m, f)
                mock_choice.assert_called_once()
                assert result is m


class TestDetermineName:
    @pytest.mark.parametrize(
        "first,second",
        [
            pytest.param("rockitten", "aquapup", id="normal_vowel_blend"),
            pytest.param("flare", "storm", id="short_words"),
            pytest.param("xyz", "qrs", id="no_vowels_fallback"),
            pytest.param("a", "b", id="single_chars"),
            pytest.param("ae", "io", id="all_vowels"),
            pytest.param("rockitten", "rockitten", id="identical_words"),
        ],
    )
    def test_name_is_nonempty_string(self, daycare, first, second):
        result = daycare._determine_name(first, second)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_name_is_capitalized(self, daycare):
        result = daycare._determine_name("rockitten", "aquapup")
        assert result[0].isupper()

    def test_no_consecutive_duplicate_chars(self, daycare):
        result = daycare._determine_name("rockitten", "aquapup")
        for i in range(1, len(result)):
            assert result[i] != result[i - 1], (
                f"Duplicate char at {i} in '{result}'"
            )

    def test_no_vowel_words_use_midpoint_split(self, daycare):
        result = daycare._determine_name("xyz", "qrs")
        assert len(result) > 0


class TestStateSerialization:
    def test_round_trip_preserves_scalars(self, daycare):
        daycare.progress_steps = 1234.5
        daycare.required_steps = 8000
        daycare.halfway_notified = True
        daycare.ready_notified = False
        daycare.training_steps_start = 42.0
        daycare.last_training_exp = 100
        daycare.last_training_cost = 50

        state = daycare.get_state()

        dc2 = Daycare(daycare.owner)
        with patch("tuxemon.entity.daycare.decode_monsters", return_value=[]):
            dc2.load_state(state)

        assert dc2.progress_steps == 1234.5
        assert dc2.required_steps == 8000
        assert dc2.halfway_notified is True
        assert dc2.ready_notified is False
        assert dc2.training_steps_start == 42.0
        assert dc2.last_training_exp == 100
        assert dc2.last_training_cost == 50

    def test_load_state_defaults_on_missing_keys(self, daycare):
        with patch("tuxemon.entity.daycare.decode_monsters", return_value=[]):
            daycare.load_state({})
        assert daycare.progress_steps == 0
        assert daycare.required_steps == 10000
        assert daycare.halfway_notified is False
        assert daycare.ready_notified is False
