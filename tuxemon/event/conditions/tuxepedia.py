# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from tuxemon.db import MonsterModel, SeenStatus, db
from tuxemon.event import MapCondition
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session
from tuxemon.tools import compare

lookup_cache: dict[str, MonsterModel] = {}


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

    name = "tuxepedia"

    def test(self, session: Session, condition: MapCondition) -> bool:
        if not lookup_cache:
            _lookup_monsters()

        player = session.player
        operator, value, *_total = condition.parameters

        if _total:
            total = int(_total[0])
        else:
            total = len(lookup_cache)

        tuxepedia = list(player.tuxepedia.values())
        caught = tuxepedia.count(SeenStatus.caught)
        seen = tuxepedia.count(SeenStatus.seen) + caught
        percentage = round((seen / total) * 100, 1)

        if not 0.0 <= float(value) <= 100.0:
            raise ValueError(f"{value} must be between 0.0 and 100.0")

        return compare(operator, percentage, float(value))


def _lookup_monsters() -> None:
    monsters = list(db.database["monster"])
    for mon in monsters:
        results = db.lookup(mon, table="monster")
        if results.txmn_id > 0:
            lookup_cache[mon] = results
