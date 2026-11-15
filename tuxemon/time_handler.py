# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime
from random import randint
from typing import Final

from tuxemon.locale.locale import T
from tuxemon.platform.const.sizes import MONTH_KEYS
from tuxemon.user_config import CONFIG

logger = logging.getLogger(__name__)

DAY_OF_YEAR_SPRING_START: Final[int] = 81
DAY_OF_YEAR_SUMMER_START: Final[int] = 173
DAY_OF_YEAR_AUTUMN_START: Final[int] = 265
DAY_OF_YEAR_WINTER_START: Final[int] = 356


@dataclass(frozen=True)
class TimeSnapshot:
    hour: int
    day_of_year: int
    year: int
    month: int
    day: int
    weekday: str
    leap_year: str
    daytime: str
    stage_of_day: str
    season: str


def today_month_day() -> tuple[int, int]:
    """
    Returns today's (month, day) as integers.
    """
    t = date.today()
    return t.month, t.day


def random_month_day() -> tuple[int, int]:
    """
    Returns a random (month, day) pair.
    February allows up to 29 days for simplicity.
    """
    month = randint(1, 12)

    if month in (4, 6, 9, 11):
        max_days = 30
    elif month == 2:
        max_days = 29
    else:
        max_days = 31

    day = randint(1, max_days)
    return month, day


class TimeHandler:
    """
    Real-world time handler.
    Always reflects the actual system clock.
    No simulation, no time multiplier, no internal progression.
    """

    def __init__(self, hemisphere: str = CONFIG.hemisphere) -> None:
        self.hemisphere: str = hemisphere.lower()

    @property
    def today_string(self) -> str:
        month, day = self.get_month_day()

        if 1 <= month <= 12:
            month_name = T.translate(MONTH_KEYS[month - 1])
            return f"{month_name} {day}"

        return ""

    def get_current_time(self) -> datetime:
        """Returns the real current datetime."""
        return datetime.now()

    def get_ordinal(self) -> int:
        return self.get_current_time().toordinal()

    def get_time_variables(self) -> TimeSnapshot:
        t = self.get_current_time()
        year = t.year

        return TimeSnapshot(
            hour=t.hour,
            day_of_year=t.timetuple().tm_yday,
            year=year,
            month=t.month,
            day=t.day,
            weekday=t.strftime("%A").lower(),
            leap_year="true" if self.is_leap_year(year) else "false",
            daytime=self._get_day_night_cycle(t),
            stage_of_day=self._get_stage_of_day(t),
            season=self._get_season(t),
        )

    @staticmethod
    def is_leap_year(year: int) -> bool:
        """Returns True if the given year is a leap year."""
        return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)

    def get_month_day(self) -> tuple[int, int]:
        t = self.get_current_time()
        return (t.month, t.day)

    def is_today(self, month: int, day: int) -> bool:
        t = self.get_current_time()
        return t.month == month and t.day == day

    def _get_day_night_cycle(self, t: datetime) -> str:
        """Returns 'true' for day (06:00-17:59), 'false' otherwise."""
        hour = t.hour
        return "true" if 6 <= hour < 18 else "false"

    def _get_stage_of_day(self, t: datetime) -> str:
        """Returns: dawn, morning, afternoon, dusk, or night."""
        hour = t.hour

        if 4 <= hour < 8:
            return "dawn"
        if 8 <= hour < 12:
            return "morning"
        if 12 <= hour < 16:
            return "afternoon"
        if 16 <= hour < 20:
            return "dusk"
        return "night"

    def _get_season(self, t: datetime) -> str:
        """Determines the season based on real-world day-of-year and hemisphere."""
        day = t.timetuple().tm_yday

        if self.hemisphere == "northern":
            if day < DAY_OF_YEAR_SPRING_START:
                return "winter"
            if day < DAY_OF_YEAR_SUMMER_START:
                return "spring"
            if day < DAY_OF_YEAR_AUTUMN_START:
                return "summer"
            if day < DAY_OF_YEAR_WINTER_START:
                return "autumn"
            return "winter"

        if self.hemisphere == "southern":
            if day < DAY_OF_YEAR_SPRING_START:
                return "summer"
            if day < DAY_OF_YEAR_SUMMER_START:
                return "autumn"
            if day < DAY_OF_YEAR_AUTUMN_START:
                return "winter"
            if day < DAY_OF_YEAR_WINTER_START:
                return "spring"
            return "summer"

        raise ValueError(f"Invalid hemisphere configured: {self.hemisphere}")
