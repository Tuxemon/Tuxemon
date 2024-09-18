# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import datetime as dt
from datetime import datetime

from tuxemon import prepare


def get_current_time() -> datetime:
    """Gets the current date and time"""
    return dt.datetime.now()


def calculate_day_night_cycle(time: datetime) -> str:
    """Calculates the current day/night cycle based on the time provided.

    Parameters:
        time: A datetime object representing the day/night cycle.

    Returns:
        A string (day or night).
    """
    hour = time.hour
    if hour < 6:
        return "false"
    elif 6 <= hour < 18:
        return "true"
    else:
        return "false"


def calculate_day_stage_of_day(time: datetime) -> str:
    """Calculates the stage of day cycle based on the time provided.

    Parameters:
        time: A datetime object.

    Returns:
        A string (dawn, morning, afternoon, dusk or night).
    """
    hour = time.hour
    if hour < 4:
        return "night"
    elif 4 <= hour < 8:
        return "dawn"
    elif 8 <= hour < 12:
        return "morning"
    elif 12 <= hour < 16:
        return "afternoon"
    elif 16 <= hour < 20:
        return "dusk"
    else:
        return "night"


def determine_season(
    time: datetime, hemisphere: str = prepare.NORTHERN
) -> str:
    """Determines the current season based on the time and hemisphere.

    Parameters:
        time: A datetime object representing the current time.
        hemisphere: A string representing the hemisphere.

    Returns:
        A string (winter, spring, summer or autumn).
    """
    day_of_year = time.timetuple().tm_yday
    if hemisphere == prepare.NORTHERN:
        if day_of_year < 81:
            return "winter"
        elif 81 <= day_of_year < 173:
            return "spring"
        elif 173 <= day_of_year < 265:
            return "summer"
        elif 265 <= day_of_year < 356:
            return "autumn"
        else:
            return "winter"
    elif hemisphere == prepare.SOUTHERN:
        if day_of_year < 81:
            return "summer"
        elif 81 <= day_of_year < 173:
            return "autumn"
        elif 173 <= day_of_year < 265:
            return "winter"
        elif 265 <= day_of_year < 356:
            return "spring"
        else:
            return "summer"
    else:
        raise ValueError("Invalid hemisphere")


def is_leap_year(year: int) -> bool:
    """Checks if the given year is a leap year.

    Parameters:
        year: An integer representing the year.

    Returns:
        True if the year is a leap year, False otherwise.
    """
    return (
        (year % 400 == 0)
        and (year % 100 == 0)
        or (year % 4 == 0)
        and (year % 100 != 0)
    )
