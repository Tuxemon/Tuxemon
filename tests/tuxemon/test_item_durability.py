# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import random

import pytest

from tuxemon.item.durability import Durability


@pytest.mark.parametrize(
    "max_wear, expected",
    [
        pytest.param(0, False, id="zero"),
        pytest.param(1, True, id="one"),
        pytest.param(10, True, id="ten"),
    ],
)
def test_has_wear(max_wear, expected):
    d = Durability(max_wear=max_wear)
    assert d.has_wear == expected


@pytest.mark.parametrize(
    "max_wear, current, expected",
    [
        pytest.param(0, 0, False, id="no_wear"),
        pytest.param(5, 0, False, id="fresh"),
        pytest.param(5, 4, False, id="almost"),
        pytest.param(5, 5, True, id="exact"),
        pytest.param(5, 10, True, id="over"),
    ],
)
def test_is_broken(max_wear, current, expected):
    d = Durability(max_wear=max_wear, current=current)
    assert d.is_broken == expected


@pytest.mark.parametrize(
    "max_wear, current, expected",
    [
        pytest.param(0, 0, 0.0, id="zero"),
        pytest.param(10, 0, 0.0, id="fresh"),
        pytest.param(10, 5, 0.5, id="half"),
        pytest.param(10, 10, 1.0, id="full"),
        pytest.param(10, 20, 1.0, id="over_clamp"),
        pytest.param(10, -5, 0.0, id="under_clamp"),
    ],
)
def test_ratio(max_wear, current, expected):
    d = Durability(max_wear=max_wear, current=current)
    assert d.ratio == expected


@pytest.mark.parametrize(
    "max_wear, current, amount, expected_current, expected_broke",
    [
        pytest.param(0, 0, 1, 0, False, id="no_system"),
        pytest.param(5, 0, 1, 1, False, id="normal"),
        pytest.param(5, 4, 1, 5, True, id="break_on_reach"),
        pytest.param(5, 4, 10, 5, True, id="clamped"),
        pytest.param(5, 5, 1, 5, True, id="already_broken"),
    ],
)
def test_increase_no_random(
    max_wear, current, amount, expected_current, expected_broke
):
    d = Durability(max_wear=max_wear, current=current, break_chance=0.0)
    broke = d.increase(amount)
    assert d.current == expected_current
    assert broke == expected_broke


def test_increase_random_break():
    d = Durability(max_wear=10, current=1, break_chance=1.0)
    broke = d.increase(1)
    assert broke is True
    assert d.current == d.max_wear


@pytest.mark.parametrize(
    "break_chance, random_value, expected",
    [
        pytest.param(0.0, 0.0, False, id="never"),
        pytest.param(0.5, 0.6, False, id="mid_high"),
        pytest.param(0.5, 0.4, True, id="mid_low"),
        pytest.param(1.0, 0.999, True, id="always"),
    ],
)
def test_should_break(monkeypatch, break_chance, random_value, expected):
    monkeypatch.setattr(random, "random", lambda: random_value)
    d = Durability(max_wear=5, break_chance=break_chance)
    assert d.should_break() == expected


def test_reset():
    d = Durability(max_wear=10, current=7)
    d.reset()
    assert d.current == 0


@pytest.mark.parametrize(
    "current, amount, expected",
    [
        pytest.param(5, -1, 0, id="full repair"),
        pytest.param(5, 0, 5, id="none"),
        pytest.param(5, 2, 3, id="partial"),
        pytest.param(5, 10, 0, id="clamped"),
    ],
)
def test_repair(current, amount, expected):
    d = Durability(max_wear=10, current=current)
    d.repair(amount)
    assert d.current == expected


def test_try_increase_no_wear():
    d = Durability(max_wear=0, current=0)
    assert d.try_increase(1) is False
    assert d.current == 0


def test_try_increase_negative_amount():
    d = Durability(max_wear=5, current=2)
    assert d.try_increase(-1) is False
    assert d.current == 2


def test_try_increase_valid():
    d = Durability(max_wear=5, current=2)
    broke = d.try_increase(2)
    assert broke is False
    assert d.current == 4


def test_try_increase_breaks():
    d = Durability(max_wear=5, current=4, break_chance=0.0)
    broke = d.try_increase(1)
    assert broke is True
    assert d.current == 5


def test_try_reset_no_wear():
    d = Durability(max_wear=0, current=5)
    d.try_reset()
    assert d.current == 5


def test_try_reset_with_wear():
    d = Durability(max_wear=10, current=7)
    d.try_reset()
    assert d.current == 0


def test_try_repair_no_wear():
    d = Durability(max_wear=0, current=5)
    d.try_repair(3)
    assert d.current == 5


@pytest.mark.parametrize(
    "current, amount, expected",
    [
        pytest.param(5, -1, 0, id="full repair"),
        pytest.param(5, 0, 5, id="none"),
        pytest.param(5, 2, 3, id="partial"),
        pytest.param(5, 10, 0, id="clamped"),
    ],
)
def test_try_repair_with_wear(current, amount, expected):
    d = Durability(max_wear=10, current=current)
    d.try_repair(amount)
    assert d.current == expected


def test_try_increase_calls_increase(monkeypatch):
    d = Durability(max_wear=5, current=1)

    called = {"value": False}

    def fake_increase(amount):
        called["value"] = True
        return True

    monkeypatch.setattr(d, "increase", fake_increase)
    d.try_increase(1)

    assert called["value"] is True


def test_try_reset_calls_reset(monkeypatch):
    d = Durability(max_wear=5, current=3)

    called = {"value": False}

    def fake_reset():
        called["value"] = True

    monkeypatch.setattr(d, "reset", fake_reset)

    d.try_reset()

    assert called["value"] is True


def test_try_repair_calls_repair(monkeypatch):
    d = Durability(max_wear=5, current=3)

    called = {"value": False}

    def fake_repair(amount):
        called["value"] = True

    monkeypatch.setattr(d, "repair", fake_repair)

    d.try_repair(2)

    assert called["value"] is True
