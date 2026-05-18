# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import time

import pytest

from tuxemon.platform.combo_detector import ComboDetector, ComboProfile
from tuxemon.platform.const import buttons
from tuxemon.platform.events import PlayerInput


@pytest.fixture
def detector():
    return ComboDetector()


@pytest.fixture
def triggered_flag():
    """A mutable flag to track callback activation."""
    return {"value": False}


@pytest.fixture
def make_callback(triggered_flag):
    def _cb():
        triggered_flag["value"] = True

    return _cb


def test_combo_not_triggered_with_wrong_sequence(
    detector, make_callback, triggered_flag
):
    profile = ComboProfile(
        name="TestCombo",
        buttons=[buttons.LEFT, buttons.RIGHT, buttons.LEFT, buttons.RIGHT],
        callback=make_callback,
        delays_s=[1, 1, 1, 1],
    )
    detector.add_combo(profile)

    now = time.time()
    detector.process_input(PlayerInput(buttons.LEFT, now))
    detector.process_input(PlayerInput(buttons.UP, now + 0.2))  # wrong button
    detector.process_input(PlayerInput(buttons.LEFT, now + 0.4))
    detector.process_input(PlayerInput(buttons.RIGHT, now + 0.6))

    assert not triggered_flag["value"]


def test_multiple_combos_trigger_independently(detector):
    triggered1 = {"v": False}
    triggered2 = {"v": False}

    def cb1():
        triggered1["v"] = True

    def cb2():
        triggered2["v"] = True

    detector.add_combo(
        ComboProfile(
            name="TestCombo1",
            buttons=[buttons.LEFT, buttons.RIGHT],
            callback=cb1,
            delays_s=[1, 1],
        )
    )
    detector.add_combo(
        ComboProfile(
            name="TestCombo2",
            buttons=[buttons.A, buttons.B],
            callback=cb2,
            delays_s=[1, 1],
        )
    )

    now = time.time()
    detector.process_input(PlayerInput(buttons.LEFT, now))
    detector.process_input(PlayerInput(buttons.RIGHT, now + 0.2))
    assert triggered1["v"]

    detector.process_input(PlayerInput(buttons.A, now + 1.0))
    detector.process_input(PlayerInput(buttons.B, now + 1.2))
    assert triggered2["v"]


def test_combo_triggered_multiple_times(
    detector, make_callback, triggered_flag
):
    profile = ComboProfile(
        name="TestCombo",
        buttons=[buttons.LEFT, buttons.RIGHT],
        callback=make_callback,
        delays_s=[1, 1],
    )
    detector.add_combo(profile)

    now = time.time()
    detector.process_input(PlayerInput(buttons.LEFT, now))
    detector.process_input(PlayerInput(buttons.RIGHT, now + 0.2))
    assert triggered_flag["value"]

    triggered_flag["value"] = False
    detector.process_input(PlayerInput(buttons.LEFT, now + 2.0))
    detector.process_input(PlayerInput(buttons.RIGHT, now + 2.2))
    assert triggered_flag["value"]


def test_combo_trigger_after_irrelevant_inputs(
    detector, make_callback, triggered_flag
):
    profile = ComboProfile(
        name="TestCombo",
        buttons=[buttons.LEFT, buttons.RIGHT, buttons.LEFT, buttons.RIGHT],
        callback=make_callback,
        delays_s=[1, 1, 1, 1],
    )
    detector.add_combo(profile)

    now = time.time()
    detector.process_input(PlayerInput(buttons.UP, now))
    detector.process_input(PlayerInput(buttons.DOWN, now + 0.1))
    detector.process_input(PlayerInput(buttons.SELECT, now + 0.2))

    detector.process_input(PlayerInput(buttons.LEFT, now + 0.3))
    detector.process_input(PlayerInput(buttons.RIGHT, now + 0.5))
    detector.process_input(PlayerInput(buttons.LEFT, now + 0.7))
    detector.process_input(PlayerInput(buttons.RIGHT, now + 0.9))

    assert triggered_flag["value"]


def test_combo_trigger(detector, make_callback, triggered_flag):
    profile = ComboProfile(
        name="TestCombo",
        buttons=[buttons.LEFT, buttons.RIGHT, buttons.LEFT, buttons.RIGHT],
        callback=make_callback,
        delays_s=[1, 1, 1, 1],
    )
    detector.add_combo(profile)

    now = time.time()
    detector.process_input(PlayerInput(buttons.LEFT, now))
    detector.process_input(PlayerInput(buttons.RIGHT, now + 0.2))
    detector.process_input(PlayerInput(buttons.LEFT, now + 0.4))
    detector.process_input(PlayerInput(buttons.RIGHT, now + 0.6))

    assert triggered_flag["value"]


def test_combo_removed(detector, make_callback, triggered_flag):
    profile = ComboProfile(
        name="RemovableCombo",
        buttons=[buttons.LEFT, buttons.RIGHT],
        callback=make_callback,
    )
    detector.add_combo(profile)

    assert detector.remove_combo([buttons.LEFT, buttons.RIGHT])

    now = time.time()
    detector.process_input(PlayerInput(buttons.LEFT, now))
    detector.process_input(PlayerInput(buttons.RIGHT, now + 0.2))

    assert not triggered_flag["value"]


def test_priority_tiebreaker(detector):
    triggered = {"v": None}

    def low():
        triggered["v"] = "low"

    def high():
        triggered["v"] = "high"

    detector.add_combo(
        ComboProfile(
            name="LowPriority",
            buttons=[buttons.LEFT, buttons.RIGHT],
            callback=low,
            priority=1,
        )
    )
    detector.add_combo(
        ComboProfile(
            name="HighPriority",
            buttons=[buttons.LEFT, buttons.RIGHT],
            callback=high,
            priority=5,
        )
    )

    now = time.time()
    detector.process_input(PlayerInput(buttons.LEFT, now))
    detector.process_input(PlayerInput(buttons.RIGHT, now + 0.2))

    assert triggered["v"] == "high"


def test_combo_not_triggered_due_to_global_window():
    detector = ComboDetector(global_window_s=0.5)
    triggered = {"v": False}

    def cb():
        triggered["v"] = True

    detector.add_combo(
        ComboProfile(
            name="WindowCombo",
            buttons=[buttons.LEFT, buttons.RIGHT],
            callback=cb,
        )
    )

    t = 10.0
    detector.process_input(PlayerInput(buttons.LEFT, timestamp=t))
    detector.process_input(PlayerInput(buttons.RIGHT, timestamp=t + 1.0))

    assert not triggered["v"]


def test_combo_not_triggered_due_to_delay(
    detector, make_callback, triggered_flag
):
    profile = ComboProfile(
        name="SlowCombo",
        buttons=[buttons.LEFT, buttons.RIGHT],
        callback=make_callback,
        delays_s=[0.2],
    )
    detector.add_combo(profile)

    t = 10.0
    detector.process_input(PlayerInput(buttons.LEFT, timestamp=t))
    detector.process_input(PlayerInput(buttons.RIGHT, timestamp=t + 1.0))

    assert not triggered_flag["value"]


def test_three_button_combo_with_mixed_delays(
    detector, make_callback, triggered_flag
):
    profile = ComboProfile(
        name="TripleCombo",
        buttons=[buttons.LEFT, buttons.UP, buttons.RIGHT],
        callback=make_callback,
        delays_s=[0.5, 1.0],
    )
    detector.add_combo(profile)

    t = 20.0
    detector.process_input(PlayerInput(buttons.LEFT, timestamp=t))
    detector.process_input(PlayerInput(buttons.UP, timestamp=t + 0.4))
    detector.process_input(PlayerInput(buttons.RIGHT, timestamp=t + 1.3))

    assert triggered_flag["value"]


def test_three_button_combo_fails_due_to_second_delay(
    detector, make_callback, triggered_flag
):
    profile = ComboProfile(
        name="TripleComboFail",
        buttons=[buttons.LEFT, buttons.UP, buttons.RIGHT],
        callback=make_callback,
        delays_s=[0.5, 1.0],
    )
    detector.add_combo(profile)

    t = 30.0
    detector.process_input(PlayerInput(buttons.LEFT, timestamp=t))
    detector.process_input(PlayerInput(buttons.UP, timestamp=t + 0.4))
    detector.process_input(PlayerInput(buttons.RIGHT, timestamp=t + 2.0))

    assert not triggered_flag["value"]


def test_priority_tiebreaker_duplicate(detector):
    triggered = {"v": None}

    def high():
        triggered["v"] = "high"

    def low():
        triggered["v"] = "low"

    detector.add_combo(
        ComboProfile(
            name="LowCombo",
            buttons=[buttons.LEFT, buttons.RIGHT],
            callback=low,
            priority=1,
        )
    )
    detector.add_combo(
        ComboProfile(
            name="HighCombo",
            buttons=[buttons.LEFT, buttons.RIGHT],
            callback=high,
            priority=5,
        )
    )

    t = 50.0
    detector.process_input(PlayerInput(buttons.LEFT, timestamp=t))
    detector.process_input(PlayerInput(buttons.RIGHT, timestamp=t + 0.1))

    assert triggered["v"] == "high"


def test_combo_trigger_on_release(detector, make_callback, triggered_flag):
    profile = ComboProfile(
        name="ReleaseCombo",
        buttons=[buttons.A, buttons.B],
        callback=make_callback,
        trigger_on_release=True,
    )
    detector.add_combo(profile)

    t = 40.0
    detector.process_input(PlayerInput(buttons.A, value=1, timestamp=t))
    detector.process_input(PlayerInput(buttons.B, value=1, timestamp=t + 0.1))

    release_event = PlayerInput(buttons.B, value=0, timestamp=t + 0.3)
    detector.process_input(release_event, hold_time=5)

    assert triggered_flag["value"]
