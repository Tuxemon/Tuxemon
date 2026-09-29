# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import ClassVar

from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session
from tuxemon.time_handler import TimeSnapshot
from tuxemon.tools import compare, compare_tuple

logger = logging.getLogger(__name__)


@dataclass
class TimeIsCondition(EventCondition):
    """
    Evaluates a comparison against a real-time property provided by the
    session's TimeHandler. This allows scripts to react to the current
    hour, season, weekday, stage of day, and other time-based values.

    Script usage:
        .. code-block::

            is time_is <property>,<operation>,<value>

    Script parameters:
        property:
            The name of a time property to evaluate. Valid options include:
            "date", "hour", "day_of_year", "year", "weekday", "leap_year",
            "daytime", "month", "day", "stage_of_day", and "season".

        operation:
            A comparison operator supported by the `compare` helper
            (e.g., "equals", "not_equals", "greater_than", "less_than").

        value:
            A literal value to compare against. Numeric values are compared
            numerically (e.g., hour > 17), while non-numeric values are
            compared as strings (e.g., season equals winter).

    Example:
        .. code-block::

            is time_is hour,greater_than,17
            is time_is season,equals,winter
            is time_is stage_of_day,equals,dusk
            is time_is date,equals,4-30
    """

    name: ClassVar[str] = "time_is"
    property_name: str
    operation: str
    value: str

    def test(self, session: Session) -> bool:
        snapshot = session.time.get_time_variables()

        if self.property_name == "date":
            return self._compare_date(snapshot, self.operation, self.value)

        if not hasattr(snapshot, self.property_name):
            logger.error(f"Invalid time property '{self.property_name}'")
            return False

        value = getattr(snapshot, self.property_name)
        numeric_properties = {"hour", "day_of_year", "year", "month", "day"}

        # Numeric path
        if self.property_name in numeric_properties:
            try:
                v1 = float(value)
                v2 = float(self.value)
            except ValueError:
                logger.error(
                    f"Expected numeric value for '{self.property_name}'"
                )
                return False
            return compare(self.operation, v1, v2)

        # String path (equals / not_equals only)
        if self.operation in ("equals", "=="):
            return str(value) == self.value

        if self.operation in ("not_equals", "!="):
            return str(value) != self.value

        logger.error(
            f"Operation '{self.operation}' not valid for non-numeric property '{self.property_name}'"
        )
        return False

    def _compare_date(
        self, snapshot: TimeSnapshot, operation: str, raw_value: str
    ) -> bool:
        try:
            m1, d1 = snapshot.month, snapshot.day
            m2, d2 = map(int, raw_value.split("-"))
        except Exception:
            logger.error("Invalid date format, expected MM-DD")
            return False

        current = (m1, d1)
        target = (m2, d2)
        return compare_tuple(operation, current, target)
