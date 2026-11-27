# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session
from tuxemon.tools import compare


@dataclass
class PartyStageCondition(EventCondition):
    """
    Compare how many team monsters are at one of the given evolution stages.

    Script usage:
        .. code-block::

            is party_stage <stages>,<operator>,<count>

    Script parameters:
        stages: Evolution stages joined by colons (basic, standalone,
            stage1, stage2), e.g. "stage1:stage2".
        operator: Numeric comparison operator. Accepted values are "less_than",
            "less_or_equal", "greater_than", "greater_or_equal", "equals"
            and "not_equals".
        count: Number of team monsters to compare with.

    eg. "is party_stage stage2,greater_or_equal,6": six fully evolved
    monsters in the team.
    """

    name: ClassVar[str] = "party_stage"
    stages: str
    operator: str
    count: int

    def test(self, session: Session) -> bool:
        wanted = {s.strip() for s in self.stages.split(":") if s.strip()}
        n = sum(
            1
            for monster in session.player.monsters
            if str(getattr(monster.stage, "value", monster.stage)) in wanted
        )
        return compare(self.operator, n, int(self.count))
