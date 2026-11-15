# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from tuxemon.database.runtime import db
from tuxemon.db import MonsterModel
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session
from tuxemon.tools import compare
from tuxemon.tuxepedia.reporter import TuxepediaReporter


@dataclass
class TuxepediaCondition(EventCondition):
    """
    Check Tuxepedia's progress.

    Script usage:
        .. code-block::

            is tuxepedia <operator>,<percentage>[,total]

    Script parameters:
        operator: Numeric comparison operator. Accepted values are "less_than",
            "less_or_equal", "greater_than", "greater_or_equal", "equals"
            and "not_equals".
        percentage: Number between 0.1 and 1.0
        total: Total, by default the tot number of tuxemon.
    """

    name: ClassVar[str] = "tuxepedia"
    operator: str
    percentage: float
    total: int | None = None

    def test(self, session: Session) -> bool:
        MonsterModel.load_cache(db)
        cache = MonsterModel.get_cache()

        player = session.player

        if self.total:
            total = self.total
        else:
            total = len(cache)

        reporter = TuxepediaReporter(player.tuxepedia.data)
        completeness = reporter.get_completeness_report(total)
        registered = completeness.get("registered_percent", 0.0)

        if not 0.0 <= self.percentage <= 1.0:
            raise ValueError(
                f"{self.percentage} must be between 0.0 and 100.0"
            )

        return compare(self.operator, float(registered), self.percentage)
