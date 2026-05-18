# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import pytest

from tuxemon.platform.events import PlayerInput


@pytest.mark.parametrize(
    "kwargs, attr, expected",
    [
        pytest.param(
            dict(button=1, value=1.0, hold_time=1),
            "pressed",
            True,
            id="pressed_true",
        ),
        pytest.param(
            dict(button=1, value=1.0, hold_time=2),
            "held",
            True,
            id="held_true",
        ),
        pytest.param(
            dict(button=1, value=0.0, hold_time=1),
            "pressed",
            False,
            id="pressed_false",
        ),
        pytest.param(
            dict(button=1, value=1.0, hold_time=0),
            "held",
            True,
            id="held_true_zero",
        ),
    ],
)
def test_playerinput_properties(kwargs, attr, expected):
    inp = PlayerInput(**kwargs)
    assert getattr(inp, attr) == expected


def test_triggered_defaults_false():
    inp = PlayerInput(1, 1.0, 1)
    assert not inp.triggered


def test_triggered_can_be_set_false():
    inp = PlayerInput(1, 1.0, 2)
    inp.triggered = False
    assert not inp.triggered


# PlayerInput edge cases
def test_pressed_only_on_first_frame():
    inp = PlayerInput(1, value=1, hold_time=1)
    assert inp.pressed
    inp.hold_time = 2
    assert not inp.pressed


def test_released_only_when_value_goes_to_zero():
    inp = PlayerInput(1, value=0, previous_value=1)
    assert inp.released
    inp.previous_value = 0
    assert not inp.released


def test_is_held_with_custom_threshold():
    inp = PlayerInput(1, value=1, hold_time=3)
    inp.hold_duration = 3.0
    assert inp.is_held(2.0)
