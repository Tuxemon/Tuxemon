# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import random
from unittest.mock import patch

import pytest

from tuxemon.db import StatModel
from tuxemon.monster.stat_utils import (
    StageChange,
    apply_stat_modifiers,
    get_source_key,
)
from tuxemon.monster.stats import BasicStats, TemporaryStatBoosts


class DummyMonster:
    def __init__(self):
        self.base_stats = BasicStats(
            armour=10, dodge=5, hp=100, melee=20, ranged=15, speed=30
        )
        self.current_hp = 80
        self.hp = self.base_stats.hp
        self.temporary_stat_boosts = TemporaryStatBoosts()

    def return_stat(self, stat_type):
        return getattr(self.base_stats, stat_type)


class DummySource:
    def __init__(self, slug="dummy_source"):
        self.slug = slug


@pytest.fixture
def monster():
    return DummyMonster()


@pytest.fixture
def source():
    return DummySource()


ALL_STATS = ["armour", "dodge", "melee", "ranged", "speed", "hp"]


def boost_of(monster, stat_slug):
    """The boost the monster reads back for a stat, from every source."""
    total = monster.temporary_stat_boosts.total(monster.base_stats)
    return getattr(total, stat_slug)


def stage_of(monster, stat_slug):
    """The monster's cumulative step stage for a stat."""
    return monster.temporary_stat_boosts.get_stage(stat_slug)


@pytest.mark.parametrize(
    "stat_slug",
    [pytest.param(s, id=f"nonlinear_step_{s}") for s in ALL_STATS],
)
@patch("random.randint", return_value=2)
def test_step_based_nonlinear_all_stats(_, monster, source, stat_slug):
    modifiers = {
        stat_slug: StatModel(step=2, max_deviation=0, scaling_mode="nonlinear")
    }
    base = getattr(monster.base_stats, stat_slug)
    apply_stat_modifiers(monster, source, modifiers)
    assert stage_of(monster, stat_slug) == 2
    expected_new_value = int(base * 2.0)
    expected_boost = expected_new_value - base
    assert boost_of(monster, stat_slug) == expected_boost


@pytest.mark.parametrize(
    "stat_slug",
    [pytest.param(s, id=f"value_add_{s}") for s in ALL_STATS],
)
def test_value_based_add_all_stats(monster, source, stat_slug):
    modifiers = {
        stat_slug: StatModel(
            value=5, step=None, operation="+", max_deviation=0
        )
    }
    apply_stat_modifiers(monster, source, modifiers)
    assert boost_of(monster, stat_slug) == 5


@pytest.mark.parametrize(
    "stat_slug",
    [pytest.param(s, id=f"negative_clamp_{s}") for s in ALL_STATS],
)
def test_negative_value_clamped_all_stats(monster, source, stat_slug):
    base = getattr(monster.base_stats, stat_slug)
    modifiers = {stat_slug: StatModel(value=-999, step=None, operation="+")}
    apply_stat_modifiers(monster, source, modifiers)
    assert boost_of(monster, stat_slug) == 1 - base


@pytest.mark.parametrize(
    "stat_slug",
    [pytest.param(s, id=f"step_clamp_{s}") for s in ALL_STATS],
)
@patch("random.randint", return_value=999)
def test_step_clamping_all_stats(_, monster, source, stat_slug):
    modifiers = {
        stat_slug: StatModel(
            step=6, max_deviation=10, scaling_mode="nonlinear"
        )
    }
    apply_stat_modifiers(monster, source, modifiers)
    assert stage_of(monster, stat_slug) == 6


def test_hp_override(monster, source):
    modifiers = {"current_hp": StatModel(overridetofull=True)}
    apply_stat_modifiers(monster, source, modifiers)
    assert monster.current_hp == monster.base_stats.hp


def test_current_hp_value_based(monster, source):
    modifiers = {"current_hp": StatModel(value=10, step=None, operation="-")}
    apply_stat_modifiers(monster, source, modifiers)
    assert monster.current_hp == 70


@patch("random.randint", return_value=-2)
def test_current_hp_step_based(_, monster, source):
    """Runtime health changes at once; it has no stage to accumulate."""
    modifiers = {"current_hp": StatModel(step=-2, scaling_mode="nonlinear")}
    apply_stat_modifiers(monster, source, modifiers)
    assert monster.current_hp == round(80 * (2 / 4))


@pytest.mark.parametrize(
    "stat_slug",
    [pytest.param(s, id=f"linear_step_{s}") for s in ALL_STATS],
)
@patch("random.randint", return_value=2)
def test_step_based_linear_all_stats(_, monster, source, stat_slug):
    modifiers = {
        stat_slug: StatModel(step=2, max_deviation=0, scaling_mode="linear")
    }
    base = getattr(monster.base_stats, stat_slug)
    apply_stat_modifiers(monster, source, modifiers)
    assert stage_of(monster, stat_slug) == 2
    multiplier = 1 + (2 / 6)
    expected_new_value = int(base * multiplier)
    expected_boost = expected_new_value - base
    assert boost_of(monster, stat_slug) == expected_boost


@pytest.mark.parametrize(
    "stat_slug",
    [pytest.param(s, id=f"linear_negative_{s}") for s in ALL_STATS],
)
@patch("random.randint", return_value=-3)
def test_step_based_linear_negative(_, monster, source, stat_slug):
    modifiers = {
        stat_slug: StatModel(step=-3, max_deviation=0, scaling_mode="linear")
    }
    base = getattr(monster.base_stats, stat_slug)
    apply_stat_modifiers(monster, source, modifiers)
    assert stage_of(monster, stat_slug) == -3
    multiplier = 1 + (-3 / 6)
    expected_new_value = int(base * multiplier)
    expected_boost = expected_new_value - base
    assert boost_of(monster, stat_slug) == expected_boost


@pytest.mark.parametrize(
    "stat_slug",
    [pytest.param(s, id=f"linear_dev_{s}") for s in ALL_STATS],
)
@patch("random.randint", return_value=5)
def test_step_based_linear_with_deviation(_, monster, source, stat_slug):
    modifiers = {
        stat_slug: StatModel(step=2, max_deviation=10, scaling_mode="linear")
    }
    base = getattr(monster.base_stats, stat_slug)
    apply_stat_modifiers(monster, source, modifiers)
    assert stage_of(monster, stat_slug) == 5
    multiplier = 1 + (5 / 6)
    expected_new_value = int(base * multiplier)
    expected_boost = expected_new_value - base
    assert boost_of(monster, stat_slug) == expected_boost


@pytest.mark.parametrize(
    "stat_slug",
    [pytest.param(s, id=f"linear_clamp_{s}") for s in ALL_STATS],
)
@patch("random.randint", return_value=999)
def test_step_based_linear_clamping(_, monster, source, stat_slug):
    modifiers = {
        stat_slug: StatModel(step=6, max_deviation=10, scaling_mode="linear")
    }
    apply_stat_modifiers(monster, source, modifiers)
    assert stage_of(monster, stat_slug) == 6


@patch("random.randint", return_value=2)
def test_step_based_linear_hp(_, monster, source):
    modifiers = {
        "hp": StatModel(step=2, max_deviation=0, scaling_mode="linear")
    }
    base = monster.base_stats.hp
    apply_stat_modifiers(monster, source, modifiers)
    assert stage_of(monster, "hp") == 2
    multiplier = 1 + (2 / 6)
    expected_new_value = int(base * multiplier)
    expected_boost = expected_new_value - base
    assert boost_of(monster, "hp") == expected_boost


@pytest.mark.parametrize(
    "stat_slug",
    [pytest.param(s, id=f"stack_pos_{s}") for s in ALL_STATS],
)
def test_stacking_positive(monster, source, stat_slug):
    base = getattr(monster.base_stats, stat_slug)
    with patch("random.randint", return_value=2):
        apply_stat_modifiers(
            monster,
            source,
            {stat_slug: StatModel(step=2, scaling_mode="nonlinear")},
        )
    with patch("random.randint", return_value=3):
        apply_stat_modifiers(
            monster,
            source,
            {stat_slug: StatModel(step=3, scaling_mode="nonlinear")},
        )
    assert stage_of(monster, stat_slug) == 5
    expected_new_value = int(base * (7 / 2))
    expected_boost = expected_new_value - base
    assert boost_of(monster, stat_slug) == expected_boost


@pytest.mark.parametrize(
    "stat_slug",
    [pytest.param(s, id=f"stack_neg_{s}") for s in ALL_STATS],
)
def test_stacking_negative(monster, source, stat_slug):
    base = getattr(monster.base_stats, stat_slug)
    with patch("random.randint", return_value=-2):
        apply_stat_modifiers(
            monster,
            source,
            {stat_slug: StatModel(step=-2, scaling_mode="nonlinear")},
        )
    with patch("random.randint", return_value=-3):
        apply_stat_modifiers(
            monster,
            source,
            {stat_slug: StatModel(step=-3, scaling_mode="nonlinear")},
        )
    assert stage_of(monster, stat_slug) == -5
    expected_new_value = int(base * (2 / 7))
    expected_boost = max(expected_new_value - base, 1 - base)
    assert boost_of(monster, stat_slug) == expected_boost


@pytest.mark.parametrize(
    "stat_slug",
    [pytest.param(s, id=f"stack_mix_{s}") for s in ALL_STATS],
)
def test_stacking_mixed(monster, source, stat_slug):
    base = getattr(monster.base_stats, stat_slug)
    with patch("random.randint", return_value=4):
        apply_stat_modifiers(
            monster,
            source,
            {stat_slug: StatModel(step=4, scaling_mode="nonlinear")},
        )
    with patch("random.randint", return_value=-3):
        apply_stat_modifiers(
            monster,
            source,
            {stat_slug: StatModel(step=-3, scaling_mode="nonlinear")},
        )
    assert stage_of(monster, stat_slug) == 1
    expected_new_value = int(base * (3 / 2))
    expected_boost = expected_new_value - base
    assert boost_of(monster, stat_slug) == expected_boost


@pytest.mark.parametrize(
    "stat_slug",
    [pytest.param(s, id=f"stack_clamp_{s}") for s in ALL_STATS],
)
def test_stacking_clamping(monster, source, stat_slug):
    with patch("random.randint", return_value=4):
        apply_stat_modifiers(
            monster,
            source,
            {stat_slug: StatModel(step=4, scaling_mode="nonlinear")},
        )
    with patch("random.randint", return_value=4):
        apply_stat_modifiers(
            monster,
            source,
            {stat_slug: StatModel(step=4, scaling_mode="nonlinear")},
        )
    assert stage_of(monster, stat_slug) == 6


@pytest.mark.parametrize(
    "stat_slug",
    [pytest.param(s, id=f"stack_clamp_neg_{s}") for s in ALL_STATS],
)
def test_stacking_clamping_negative(monster, source, stat_slug):
    with patch("random.randint", return_value=-4):
        apply_stat_modifiers(
            monster,
            source,
            {stat_slug: StatModel(step=-4, scaling_mode="nonlinear")},
        )
    with patch("random.randint", return_value=-4):
        apply_stat_modifiers(
            monster,
            source,
            {stat_slug: StatModel(step=-4, scaling_mode="nonlinear")},
        )
    assert stage_of(monster, stat_slug) == -6


@pytest.mark.parametrize(
    "stat_slug",
    [pytest.param(s, id=f"reset_{s}") for s in ALL_STATS],
)
def test_reset_cleanup(monster, source, stat_slug):
    with patch("random.randint", return_value=2):
        apply_stat_modifiers(
            monster,
            source,
            {stat_slug: StatModel(step=2, scaling_mode="nonlinear")},
        )
    assert stage_of(monster, stat_slug) == 2
    monster.temporary_stat_boosts.clear()
    for s in ALL_STATS:
        assert boost_of(monster, s) == 0
        assert stage_of(monster, s) == 0
    assert monster.temporary_stat_boosts.is_empty()


# Unified stages: every source moves the same stage


@pytest.mark.parametrize(
    "stat_slug",
    [pytest.param(s, id=f"shared_stage_{s}") for s in ALL_STATS],
)
def test_sources_share_one_stage(monster, stat_slug):
    """Two sources raising a stat by 2 make one +4 stage, not two boosts."""
    base = getattr(monster.base_stats, stat_slug)
    modifiers = {stat_slug: StatModel(step=2, scaling_mode="nonlinear")}

    with patch("random.randint", return_value=2):
        for slug in ("first_source", "second_source"):
            apply_stat_modifiers(monster, DummySource(slug), modifiers)

    assert stage_of(monster, stat_slug) == 4
    assert boost_of(monster, stat_slug) == int(base * (6 / 2)) - base


@pytest.mark.parametrize(
    "stat_slug",
    [pytest.param(s, id=f"shared_cap_{s}") for s in ALL_STATS],
)
def test_the_shared_stage_stops_at_the_step_limit(monster, stat_slug):
    """Piling on more sources cannot push a stat past the cap."""
    base = getattr(monster.base_stats, stat_slug)
    modifiers = {stat_slug: StatModel(step=2, scaling_mode="nonlinear")}

    with patch("random.randint", return_value=2):
        for index in range(6):
            apply_stat_modifiers(
                monster, DummySource(f"src_{index}"), modifiers
            )

    assert stage_of(monster, stat_slug) == 6
    assert boost_of(monster, stat_slug) == int(base * (8 / 2)) - base


@pytest.mark.parametrize(
    "stat_slug",
    [pytest.param(s, id=f"shared_debuff_{s}") for s in ALL_STATS],
)
def test_debuffs_from_two_sources_share_one_stage(monster, stat_slug):
    base = getattr(monster.base_stats, stat_slug)
    modifiers = {stat_slug: StatModel(step=-2, scaling_mode="nonlinear")}

    with patch("random.randint", return_value=-2):
        for slug in ("first_source", "second_source"):
            apply_stat_modifiers(monster, DummySource(slug), modifiers)

    assert stage_of(monster, stat_slug) == -4
    expected = max(int(base * (2 / 6)) - base, 1 - base)
    assert boost_of(monster, stat_slug) == expected


# Withdrawing one source


@pytest.mark.parametrize(
    "stat_slug",
    [pytest.param(s, id=f"withdraw_{s}") for s in ALL_STATS],
)
def test_withdraw_takes_back_only_that_source(monster, stat_slug):
    first = DummySource("first_source")
    second = DummySource("second_source")
    modifiers = {stat_slug: StatModel(step=2, scaling_mode="nonlinear")}

    with patch("random.randint", return_value=2):
        for src in (first, second):
            apply_stat_modifiers(monster, src, modifiers)
    assert stage_of(monster, stat_slug) == 4

    monster.temporary_stat_boosts.withdraw(get_source_key(first))

    base = getattr(monster.base_stats, stat_slug)
    assert stage_of(monster, stat_slug) == 2
    assert boost_of(monster, stat_slug) == int(base * 2.0) - base


@pytest.mark.parametrize(
    "stat_slug",
    [pytest.param(s, id=f"withdraw_flat_{s}") for s in ALL_STATS],
)
def test_withdraw_takes_back_flat_boosts(monster, stat_slug):
    first = DummySource("first_source")
    second = DummySource("second_source")

    for src in (first, second):
        apply_stat_modifiers(
            monster,
            src,
            {stat_slug: StatModel(value=5, step=None, operation="+")},
        )
    assert boost_of(monster, stat_slug) == 10

    monster.temporary_stat_boosts.withdraw(get_source_key(first))
    assert boost_of(monster, stat_slug) == 5


def test_withdraw_at_the_cap_gives_back_only_what_it_took(monster):
    """A source blocked by the cap cannot refund stages it never added."""
    modifiers = {"melee": StatModel(step=6, scaling_mode="nonlinear")}
    first = DummySource("first_source")
    second = DummySource("second_source")

    with patch("random.randint", return_value=6):
        apply_stat_modifiers(monster, first, modifiers)
        apply_stat_modifiers(monster, second, modifiers)
    assert stage_of(monster, "melee") == 6

    monster.temporary_stat_boosts.withdraw(get_source_key(second))
    assert stage_of(monster, "melee") == 6


def test_withdraw_of_an_unknown_source_is_harmless(monster, source):
    apply_stat_modifiers(
        monster, source, {"melee": StatModel(step=2, scaling_mode="nonlinear")}
    )
    monster.temporary_stat_boosts.withdraw("nothing:here")
    assert stage_of(monster, "melee") == 2


def test_boosts_follow_a_change_in_base_stats(monster, source):
    """Boosts are derived on read, not frozen when they were applied."""
    with patch("random.randint", return_value=2):
        apply_stat_modifiers(
            monster,
            source,
            {"melee": StatModel(step=2, scaling_mode="nonlinear")},
        )
    assert boost_of(monster, "melee") == 20

    monster.base_stats.melee = 50
    assert boost_of(monster, "melee") == 50


def test_invalid_stat_name_rejected(monster):
    with pytest.raises(ValueError):
        monster.temporary_stat_boosts.add_flat("source", "current_hp", 5)
    with pytest.raises(ValueError):
        monster.temporary_stat_boosts.get_stage("nonsense")


def test_stress_100_random(monster, source):
    for _ in range(100):
        stat_slug = random.choice(ALL_STATS)
        if random.random() < 0.7:
            step = random.randint(-6, 6)
            max_dev = random.randint(0, 3)
            scaling_mode = random.choice(["linear", "nonlinear"])
            model = StatModel(
                step=step, max_deviation=max_dev, scaling_mode=scaling_mode
            )
        else:
            value = random.randint(-20, 20)
            max_dev = random.randint(0, 5)
            op = random.choice(["+", "-", "*", "/"])
            model = StatModel(
                value=value, step=None, max_deviation=max_dev, operation=op
            )

        apply_stat_modifiers(monster, source, {stat_slug: model})

        assert -6 <= stage_of(monster, stat_slug) <= 6

        if stat_slug != "current_hp":
            boost = boost_of(monster, stat_slug)
            base = getattr(monster.base_stats, stat_slug)
            assert base + boost >= 1

        assert 0 <= monster.current_hp <= monster.base_stats.hp


# What a modifier reports back, so the player can be told


def test_step_modifiers_report_the_stages_they_moved(monster, source):
    with patch("random.randint", return_value=2):
        changes = apply_stat_modifiers(
            monster,
            source,
            {
                "melee": StatModel(step=2, scaling_mode="nonlinear"),
                "speed": StatModel(step=2, scaling_mode="nonlinear"),
            },
        )

    assert changes == [StageChange("melee", 2), StageChange("speed", 2)]


def test_a_modifier_reports_only_what_the_cap_allowed(monster, source):
    """At stage 5 a +2 step can only move 1, and at 6 it moves nothing."""
    with patch("random.randint", return_value=5):
        apply_stat_modifiers(
            monster,
            source,
            {"melee": StatModel(step=5, scaling_mode="nonlinear")},
        )

    with patch("random.randint", return_value=2):
        changes = apply_stat_modifiers(
            monster,
            source,
            {"melee": StatModel(step=2, scaling_mode="nonlinear")},
        )
    assert changes == [StageChange("melee", 1)]

    with patch("random.randint", return_value=2):
        changes = apply_stat_modifiers(
            monster,
            source,
            {"melee": StatModel(step=2, scaling_mode="nonlinear")},
        )
    assert changes == []


def test_value_modifiers_report_no_stage(monster, source):
    """A flat addition moves no stage, so there is no "rose" to report."""
    changes = apply_stat_modifiers(
        monster,
        source,
        {"melee": StatModel(value=5, step=None, operation="+")},
    )
    assert changes == []


def test_current_hp_reports_no_stage(monster, source):
    with patch("random.randint", return_value=-2):
        changes = apply_stat_modifiers(
            monster,
            source,
            {"current_hp": StatModel(step=-2, scaling_mode="nonlinear")},
        )
    assert changes == []
