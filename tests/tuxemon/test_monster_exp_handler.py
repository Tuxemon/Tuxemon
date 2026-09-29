# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import pytest

from tuxemon.database.rules import config_monster
from tuxemon.monster.experience import MonsterExperience


class MockConfig:
    def __init__(self):
        self.experience_groups = {
            "default": {"multiplier": 1.0, "experience_coefficient": 3},
            "fast": {"multiplier": 0.8, "experience_coefficient": 2.5},
            "slow": {"multiplier": 1.25, "experience_coefficient": 3.5},
        }


mock_config = MockConfig()


@pytest.fixture
def monster():
    return MonsterExperience()


def test_initialization_defaults(monster):
    assert monster.level == 1
    assert monster.total_experience == 0
    assert monster.experience_modifier == 1.0
    assert not monster.got_experience
    assert not monster.levelling_up
    assert not monster.is_maxed_out


def test_set_level_within_bounds(monster):
    monster.set_level(10)
    assert monster.level == 10
    assert monster.total_experience > 0


def test_set_level_above_max(monster):
    monster.set_level(config_monster.level_range[1] + 10)
    assert monster.level == config_monster.level_range[1]


def test_experience_required_default_group():
    m = MonsterExperience(level=5)
    required = m.experience_required()
    assert required == int(1.0 * (5**3))


def test_experience_required_with_offset():
    m = MonsterExperience(level=5)
    required = m.experience_required(level_delta=2)
    assert required == int(1.0 * (7**3))


def test_give_experience_and_level_up():
    m = MonsterExperience(level=1)
    exp_to_next = m.experience_required(level_delta=1)
    gained = m.give_experience(exp_to_next)
    assert gained == 1
    assert m.level == 2


def test_give_experience_to_max_level():
    m = MonsterExperience(level=config_monster.level_range[1] - 1)
    m.give_experience(9999999)
    assert m.level == config_monster.level_range[1]
    assert m.is_maxed_out


def test_excess_experience_at_max_level():
    m = MonsterExperience(level=config_monster.level_range[1])
    m._total_experience = m.experience_required() + 500
    assert m.excess_experience() == 500


def test_set_exp_group_valid(monster):
    monster.set_exp_group("fast")
    assert monster._exp_group_slug == "fast"


def test_set_exp_group_invalid(monster):
    with pytest.raises(ValueError):
        monster.set_exp_group("unknown")


def test_give_zero_experience(monster):
    gained = monster.give_experience(0)
    assert gained == 0
    assert monster.level == 1


def test_negative_experience_gain():
    m = MonsterExperience(level=5, total_experience=1000)
    gained = m.give_experience(-500)
    assert gained == 0
    assert m.total_experience >= 0


def test_multiple_level_ups():
    m = MonsterExperience(level=1)
    exp_to_5 = m.experience_required(level_delta=4)
    gained = m.give_experience(exp_to_5)
    assert m.level == 5
    assert gained == 4


def test_experience_required_at_max_level():
    m = MonsterExperience(level=config_monster.level_range[1])
    required = m.experience_required(level_delta=1)
    assert required > 0
    assert m.is_maxed_out


def test_invalid_exp_group_fallback():
    m = MonsterExperience(level=5)
    m._exp_group_slug = "nonexistent"
    required = m.experience_required()

    expected = mock_config.experience_groups["default"]["multiplier"] * (
        5 ** mock_config.experience_groups["default"]["experience_coefficient"]
    )
    assert required == int(expected)


def test_experience_modifier_applied():
    m = MonsterExperience(level=1)
    m._experience_modifier = 2.0
    base = m.experience_required(level_delta=1)
    m.give_experience(base // 2)
    assert m.level == 2


def test_is_maxed_out_property():
    low = MonsterExperience(level=config_monster.level_range[1] - 1)
    assert not low.is_maxed_out

    maxed = MonsterExperience(level=config_monster.level_range[1])
    assert maxed.is_maxed_out

    m = MonsterExperience()
    m.set_level(config_monster.level_range[1])
    assert m.is_maxed_out


def test_set_level_below_min():
    m = MonsterExperience(level=10)
    m.set_level(0)
    assert m.level == 1
    m.set_level(-5)
    assert m.level == 1


def test_set_level_resets_progress():
    m = MonsterExperience(level=1)
    m.experience_required(level_delta=3)
    exp5 = m.experience_required(level_delta=4)

    m._total_experience = exp5 - 1
    m.set_level(3)

    expected = int(1.0 * (3**3))
    assert m.level == 3
    assert m.total_experience == expected
    assert m.total_experience == m.experience_required()


def test_experience_required_slow_group():
    m = MonsterExperience(level=5, exp_group_slug="slow")
    m.config_monster = mock_config
    required = m.experience_required()
    assert required == int(1.25 * (5**3.5))


def test_experience_required_fast_group():
    m = MonsterExperience(level=10, exp_group_slug="fast")
    m.config_monster = mock_config
    required = m.experience_required(level_delta=-1)
    assert required == int(0.8 * (9**2.5))


def test_level_up_flag_set():
    m = MonsterExperience(level=1)
    assert not m.levelling_up
    exp_to_next = m.experience_required(level_delta=1)
    m.give_experience(exp_to_next - m.total_experience + 1)
    assert m.levelling_up


def test_excess_experience_not_maxed_out():
    m = MonsterExperience(level=10)
    req = m.experience_required()
    m._total_experience = req + 500

    if m.level < config_monster.level_range[1]:
        assert m.excess_experience() == 0
