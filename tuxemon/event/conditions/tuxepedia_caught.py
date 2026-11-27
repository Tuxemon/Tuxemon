# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session
from tuxemon.tools import compare


@dataclass
class TuxepediaCaughtCondition(EventCondition):
    """
    Compare the number of species the player has caught (Tuxepedia).

    Script usage:
        .. code-block::

            is tuxepedia_caught <operator>,<count>

    Script parameters:
        operator: Numeric comparison operator. Accepted values are "less_than",
            "less_or_equal", "greater_than", "greater_or_equal", "equals"
            and "not_equals".
        count: Number of caught species to compare with.

    eg. "is tuxepedia_caught greater_or_equal,10": at least 10 different
    species caught (a species only seen does not count).
    """

    name: ClassVar[str] = "tuxepedia_caught"
    operator: str
    count: int

    def test(self, session: Session) -> bool:
        caught = session.player.tuxepedia.get_caught_count()
        return compare(self.operator, caught, int(self.count))
