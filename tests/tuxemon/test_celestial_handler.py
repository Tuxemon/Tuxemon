# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from dataclasses import dataclass
from typing import Any

import pytest

from tuxemon.celestial_handler import (
    CelestialCycle,
    CelestialHandler,
    get_celestial_phase,
    validate_celestial_data,
    validate_phase_lengths,
)


@dataclass
class FakeTimeSnapshot:
    day_of_year: int


class FakeTimeHandler:
    def __init__(self, day: int):
        self._day = day

    def get_time_variables(self):
        return FakeTimeSnapshot(day_of_year=self._day)


@dataclass
class FakeSession:
    time: Any


# ---------------------------------------------------------------------------
# get_celestial_phase
# ---------------------------------------------------------------------------


def test_get_celestial_phase_basic():
    cycle = CelestialCycle(
        name="basic",
        length=365,
        phase_data=[
            (100, "phase_a"),
            (100, "phase_b"),
            (165, "phase_c"),
        ],
    )

    assert get_celestial_phase(0, cycle) == "phase_a"
    assert get_celestial_phase(50, cycle) == "phase_a"
    assert get_celestial_phase(150, cycle) == "phase_b"
    assert get_celestial_phase(250, cycle) == "phase_c"


def test_get_celestial_phase_wraparound():
    cycle = CelestialCycle(
        name="wrap",
        length=365,
        phase_data=[
            (200, "long_phase"),
            (165, "short_phase"),
        ],
    )

    # 365 % 365 == 0 → long_phase
    assert get_celestial_phase(365, cycle) == "long_phase"
    # 366 % 365 == 1 → long_phase
    assert get_celestial_phase(366, cycle) == "long_phase"
    # 530 % 365 == 165 → still in long_phase (0–199)
    assert get_celestial_phase(530, cycle) == "long_phase"


def test_get_celestial_phase_negative_days():
    cycle = CelestialCycle(
        name="neg",
        length=365,
        phase_data=[(200, "a"), (165, "b")],
    )

    # -1 % 365 == 364 → in "b"
    assert get_celestial_phase(-1, cycle) == "b"
    # -200 % 365 == 165 → in "a"
    assert get_celestial_phase(-200, cycle) == "a"


def test_get_celestial_phase_length_one_cycle():
    cycle = CelestialCycle(
        name="single",
        length=1,
        phase_data=[(1, "only")],
    )

    for day in [0, 1, 2, 10, -1, -10]:
        assert get_celestial_phase(day, cycle) == "only"


def test_get_celestial_phase_multiple_lengths():
    cycle = CelestialCycle(
        name="multi",
        length=10,
        phase_data=[
            (5, "x"),
            (5, "y"),
        ],
    )

    # 0–4 → x, 5–9 → y
    assert get_celestial_phase(0, cycle) == "x"
    assert get_celestial_phase(4, cycle) == "x"
    assert get_celestial_phase(5, cycle) == "y"
    assert get_celestial_phase(9, cycle) == "y"
    # wrap
    assert get_celestial_phase(12, cycle) == "x"  # 12 % 10 == 2


# ---------------------------------------------------------------------------
# validation helpers
# ---------------------------------------------------------------------------


def test_validate_phase_lengths_valid():
    data = [(200, "a"), (165, "b")]
    validate_phase_lengths("ok", 365, data)  # should not raise


def test_validate_phase_lengths_invalid_total():
    data = [(100, "a"), (100, "b")]  # total 200, expected 365
    with pytest.raises(ValueError):
        validate_phase_lengths("bad", 365, data)


def test_validate_phase_lengths_zero_length_cycle():
    data = [(0, "a")]
    # depending on your implementation, you may want to forbid length <= 0
    # here we assert that mismatched total vs length raises
    with pytest.raises(ValueError):
        validate_phase_lengths("zero", 0, data)


def test_validate_celestial_data_valid():
    cycle = CelestialCycle(
        name="moon",
        length=365,
        phase_data=[(200, "waxing"), (165, "waning")],
    )
    validate_celestial_data(cycle)  # should not raise


def test_validate_celestial_data_invalid():
    cycle = CelestialCycle(
        name="moon",
        length=365,
        phase_data=[(300, "a"), (10, "b")],  # total 310
    )
    with pytest.raises(ValueError):
        validate_celestial_data(cycle)


# ---------------------------------------------------------------------------
# CelestialHandler
# ---------------------------------------------------------------------------


def test_celestial_handler_get_phase():
    cycles = [
        CelestialCycle(
            name="moon",
            length=365,
            phase_data=[(200, "waxing"), (165, "waning")],
        )
    ]

    session = FakeSession(time=FakeTimeHandler(day=50))
    handler = CelestialHandler(session=session, _cycles=cycles)

    assert handler.get_phase("moon") == "waxing"


def test_celestial_handler_get_all_phases():
    cycles = [
        CelestialCycle("moon", 365, [(200, "waxing"), (165, "waning")]),
        CelestialCycle("sun", 365, [(365, "high")]),
    ]

    session = FakeSession(time=FakeTimeHandler(day=250))
    handler = CelestialHandler(session=session, _cycles=cycles)

    phases = handler.get_all_phases()
    assert phases == {"moon": "waning", "sun": "high"}


def test_celestial_handler_iter_phases():
    cycles = [
        CelestialCycle("moon", 365, [(200, "waxing"), (165, "waning")]),
        CelestialCycle("sun", 365, [(365, "high")]),
    ]

    session = FakeSession(time=FakeTimeHandler(day=10))
    handler = CelestialHandler(session=session, _cycles=cycles)

    result = dict(handler.iter_phases())
    assert result == {"moon": "waxing", "sun": "high"}


def test_celestial_handler_unknown_body():
    cycles = [
        CelestialCycle("moon", 365, [(365, "full")]),
    ]

    session = FakeSession(time=FakeTimeHandler(day=10))
    handler = CelestialHandler(session=session, _cycles=cycles)

    with pytest.raises(KeyError):
        handler.get_phase("sun")


def test_celestial_handler_cache_behavior():
    cycles = [
        CelestialCycle("moon", 365, [(365, "full")]),
    ]

    session = FakeSession(time=FakeTimeHandler(day=10))
    handler = CelestialHandler(session=session, _cycles=cycles)

    first = handler.get_all_phases()
    second = handler.get_all_phases()

    # same dict instance if cache is used
    assert first is second


def test_celestial_handler_multiple_lengths():
    cycles = [
        CelestialCycle("moon", 365, [(200, "waxing"), (165, "waning")]),
        CelestialCycle("weird", 10, [(5, "x"), (5, "y")]),
    ]

    session = FakeSession(time=FakeTimeHandler(day=12))
    handler = CelestialHandler(session=session, _cycles=cycles)

    assert handler.get_phase("moon") == "waxing"
    # 12 % 10 == 2 → in first phase "x"
    assert handler.get_phase("weird") == "x"
