# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock, patch

import pytest

from tuxemon.database.rules import config_capture
from tuxemon.formula import (
    calculate_status_modifier,
    capture,
    shake_check,
)
from tuxemon.monster.monster import Monster
from tuxemon.monster.status import MonsterStatusHandler

# shake_check tests


@pytest.fixture
def basic_target():
    t = MagicMock(spec=Monster)
    t.hp = 100
    t.current_hp = 50
    t.catch_rate = 100
    t.lower_catch_resistance = 0.9
    t.upper_catch_resistance = 1.1
    return t


@patch("random.uniform")
def test_shake_check_basic(mock_uniform, basic_target):
    mock_uniform.return_value = 1.0
    result = shake_check(basic_target, 1.0, 1.0)
    assert isinstance(result, float)
    assert result > 0


@patch("random.uniform")
def test_shake_check_different_values(mock_uniform):
    mock_uniform.return_value = 0.5

    target = MagicMock(spec=Monster)
    target.hp = 150
    target.current_hp = 25
    target.catch_rate = 200
    target.lower_catch_resistance = 0.8
    target.upper_catch_resistance = 1.2

    result = shake_check(target, 1.5, 2.0)
    assert isinstance(result, float)


@patch("random.uniform")
def test_shake_check_edge_cases(mock_uniform):
    mock_uniform.return_value = 1.0

    # Normal case
    t1 = MagicMock(spec=Monster)
    t1.hp = 100
    t1.current_hp = 50
    t1.catch_rate = 100
    t1.lower_catch_resistance = 0.9
    t1.upper_catch_resistance = 1.1
    assert isinstance(shake_check(t1, 1.0, 1.0), float)

    # Extreme low HP
    t2 = MagicMock(spec=Monster)
    t2.hp = 1000
    t2.current_hp = 1
    t2.catch_rate = 255
    t2.lower_catch_resistance = 1.0
    t2.upper_catch_resistance = 1.0
    assert isinstance(shake_check(t2, 1.0, 1.0), float)


@patch("random.uniform")
def test_shake_check_zero_hp(mock_uniform):
    mock_uniform.return_value = 1.0

    target = MagicMock(spec=Monster)
    target.hp = 100
    target.current_hp = 0
    target.catch_rate = 100
    target.lower_catch_resistance = 1.0
    target.upper_catch_resistance = 1.0

    assert isinstance(shake_check(target, 1.0, 1.0), float)


# capture tests


@pytest.fixture
def shake_divisor():
    return config_capture.shake_divisor


@pytest.fixture
def total_shakes():
    return config_capture.total_shakes


@patch("random.randint")
def test_capture_success(mock_randint, shake_divisor, total_shakes):
    mock_randint.return_value = shake_divisor // 2
    captured, shakes = capture(shake_divisor)
    assert captured
    assert shakes == total_shakes


@patch("random.randint")
def test_capture_failure_first_shake(mock_randint):
    mock_randint.return_value = config_capture.shake_divisor
    captured, shakes = capture(0)
    assert not captured
    assert shakes == 1


@patch("random.randint")
def test_capture_failure_middle_shake(mock_randint, shake_divisor):
    mock_randint.side_effect = [
        shake_divisor // 4,
        shake_divisor // 4,
        shake_divisor,
    ]
    captured, shakes = capture(shake_divisor // 4)
    assert not captured
    assert shakes == 3


@patch("random.randint")
def test_capture_failure_last_shake(mock_randint, shake_divisor, total_shakes):
    mock_randint.side_effect = [
        shake_divisor // 4,
        shake_divisor // 4,
        shake_divisor // 4,
        shake_divisor,
    ]
    captured, shakes = capture(shake_divisor // 4)
    assert not captured
    assert shakes == total_shakes


@patch("random.randint")
def test_capture_edge_case_shake_check_zero(mock_randint):
    mock_randint.return_value = config_capture.shake_divisor // 2
    captured, shakes = capture(0)
    assert not captured
    assert shakes == 1


@patch("random.randint")
def test_capture_edge_case_shake_check_max(
    mock_randint, shake_divisor, total_shakes
):
    mock_randint.return_value = shake_divisor // 2
    captured, shakes = capture(shake_divisor)
    assert captured
    assert shakes == total_shakes


# calculate_status_modifier tests


@pytest.fixture
def item():
    return MagicMock(slug="example")


@pytest.fixture
def target():
    t = MagicMock(spec=Monster, slug="mock_target")
    t.status = MonsterStatusHandler()
    return t


def test_no_config_or_status(item, target):
    assert calculate_status_modifier(item, target) == 1.0


def test_no_target_status(item, target):
    assert calculate_status_modifier(item, target) == 1.0


def test_negative_category_modifier_applied(item, target):
    target.status.status = [MagicMock(slug="unknown", category="negative")]
    assert calculate_status_modifier(item, target) == 1.2


def test_positive_category_modifier_applied(item, target):
    target.status.status = [MagicMock(slug="unknown", category="positive")]
    assert calculate_status_modifier(item, target) == 1.0


def test_multiple_status_modifiers(item, target):
    target.status.status = [
        MagicMock(slug="unknown", category="negative"),
        MagicMock(slug="name_status", category="positive"),
    ]
    expected = 0.8 * 1.2
    assert calculate_status_modifier(item, target) == expected
