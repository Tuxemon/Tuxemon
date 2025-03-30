# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from datetime import datetime

from tuxemon import prepare
from tuxemon.time_handler import (
    calculate_day_night_cycle,
    calculate_day_stage_of_day,
    determine_season,
    get_current_time,
    is_leap_year,
)


class TestTimeFunctions(unittest.TestCase):

    def test_get_current_time(self):
        current_time = get_current_time()
        self.assertIsInstance(current_time, datetime)

    def test_calculate_day_night_cycle(self):
        test_cases = [
            (datetime(2022, 1, 1, 0, 0, 0), "false"),
            (datetime(2022, 1, 1, 6, 0, 0), "true"),
            (datetime(2022, 1, 1, 18, 0, 0), "false"),
            (datetime(2022, 1, 1, 12, 0, 0), "true"),
        ]
        for time, expected in test_cases:
            self.assertEqual(calculate_day_night_cycle(time), expected)

    def test_calculate_day_stage_of_day(self):
        test_cases = [
            (datetime(2022, 1, 1, 0, 0, 0), "night"),
            (datetime(2022, 1, 1, 4, 0, 0), "dawn"),
            (datetime(2022, 1, 1, 7, 0, 0), "dawn"),
            (datetime(2022, 1, 1, 10, 0, 0), "morning"),
            (datetime(2022, 1, 1, 14, 0, 0), "afternoon"),
            (datetime(2022, 1, 1, 17, 0, 0), "dusk"),
            (datetime(2022, 1, 1, 20, 0, 0), "night"),
        ]
        for time, expected in test_cases:
            self.assertEqual(calculate_day_stage_of_day(time), expected)

    def test_determine_season(self):
        test_cases = [
            (datetime(2022, 1, 1), "winter"),
            (datetime(2022, 3, 20), "winter"),
            (datetime(2022, 6, 20), "spring"),
            (datetime(2022, 9, 20), "summer"),
            (datetime(2022, 12, 20), "autumn"),
        ]

        test_cases_southern_hemisphere = [
            (datetime(2022, 1, 1), "summer"),
            (datetime(2022, 3, 20), "summer"),
            (datetime(2022, 6, 20), "autumn"),
            (datetime(2022, 9, 20), "winter"),
            (datetime(2022, 12, 20), "spring"),
        ]

        for time, expected in test_cases:
            self.assertEqual(
                determine_season(time, hemisphere="northern"),
                expected,
            )

        for time, expected in test_cases_southern_hemisphere:
            self.assertEqual(
                determine_season(time, hemisphere="southern"),
                expected,
            )

    def test_is_leap_year(self):
        test_cases = [
            (2020, True),
            (2019, False),
            (2024, True),
            (1900, False),
            (2000, True),
        ]
        for year, expected in test_cases:
            self.assertEqual(is_leap_year(year), expected)
