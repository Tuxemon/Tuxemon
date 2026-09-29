# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from datetime import datetime

import pytest

from tuxemon.time_handler import TimeHandler, random_month_day


@pytest.fixture
def time_handler():
    return TimeHandler(hemisphere="northern")


def test_random_month_day_valid_month():
    for _ in range(500):
        month, _ = random_month_day()
        assert 1 <= month <= 12


def test_random_month_day_valid_day():
    for _ in range(500):
        month, day = random_month_day()

        if month in (4, 6, 9, 11):
            assert 1 <= day <= 30
        elif month == 2:
            assert 1 <= day <= 29
        else:
            assert 1 <= day <= 31


def test_random_month_day_distribution_runs():
    for _ in range(1000):
        random_month_day()


def test_get_current_time(time_handler):
    assert isinstance(time_handler.get_current_time(), datetime)


@pytest.mark.parametrize(
    "dt,expected",
    [
        pytest.param(datetime(2022, 1, 1, 0, 0, 0), "false", id="midnight"),
        pytest.param(datetime(2022, 1, 1, 6, 0, 0), "true", id="six_am"),
        pytest.param(datetime(2022, 1, 1, 18, 0, 0), "false", id="six_pm"),
        pytest.param(datetime(2022, 1, 1, 12, 0, 0), "true", id="noon"),
    ],
)
def test_day_night_cycle(time_handler, dt, expected):
    assert time_handler._get_day_night_cycle(dt) == expected


@pytest.mark.parametrize(
    "dt,expected",
    [
        pytest.param(
            datetime(2022, 1, 1, 0, 0, 0), "night", id="midnight_night"
        ),
        pytest.param(datetime(2022, 1, 1, 4, 0, 0), "dawn", id="early_dawn"),
        pytest.param(datetime(2022, 1, 1, 7, 0, 0), "dawn", id="late_dawn"),
        pytest.param(datetime(2022, 1, 1, 10, 0, 0), "morning", id="morning"),
        pytest.param(
            datetime(2022, 1, 1, 14, 0, 0), "afternoon", id="afternoon"
        ),
        pytest.param(datetime(2022, 1, 1, 17, 0, 0), "dusk", id="dusk"),
        pytest.param(
            datetime(2022, 1, 1, 20, 0, 0), "night", id="evening_night"
        ),
    ],
)
def test_stage_of_day(time_handler, dt, expected):
    assert time_handler._get_stage_of_day(dt) == expected


@pytest.mark.parametrize(
    "dt,expected",
    [
        pytest.param(datetime(2022, 1, 1), "winter", id="jan"),
        pytest.param(datetime(2022, 3, 20), "winter", id="mar20"),
        pytest.param(datetime(2022, 6, 20), "spring", id="jun20"),
        pytest.param(datetime(2022, 9, 20), "summer", id="sep20"),
        pytest.param(datetime(2022, 12, 20), "autumn", id="dec20"),
    ],
)
def test_season_northern(time_handler, dt, expected):
    assert time_handler._get_season(dt) == expected


@pytest.mark.parametrize(
    "dt,expected",
    [
        pytest.param(datetime(2022, 1, 1), "summer", id="jan"),
        pytest.param(datetime(2022, 3, 20), "summer", id="mar20"),
        pytest.param(datetime(2022, 6, 20), "autumn", id="jun20"),
        pytest.param(datetime(2022, 9, 20), "winter", id="sep20"),
        pytest.param(datetime(2022, 12, 20), "spring", id="dec20"),
    ],
)
def test_season_southern(dt, expected):
    handler = TimeHandler(hemisphere="southern")
    assert handler._get_season(dt) == expected


@pytest.mark.parametrize(
    "year,expected",
    [
        pytest.param(2020, True, id="2020"),
        pytest.param(2019, False, id="2019"),
        pytest.param(2024, True, id="2024"),
        pytest.param(1900, False, id="1900"),
        pytest.param(2000, True, id="2000"),
    ],
)
def test_is_leap_year(time_handler, year, expected):
    assert time_handler.is_leap_year(year) == expected


def test_get_time_variables(time_handler):
    time_handler.get_current_time = lambda: datetime(2022, 6, 20, 9, 30, 0)

    vars = time_handler.get_time_variables()

    assert vars.hour == 9
    assert vars.day_of_year == 171  # June 20, 2022
    assert vars.year == 2022
    assert vars.weekday == "monday"
    assert vars.leap_year == "false"
    assert vars.daytime == "true"
    assert vars.stage_of_day == "morning"
    assert vars.season == "spring"
