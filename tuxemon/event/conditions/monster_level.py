# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session
from tuxemon.tools import compare


@dataclass
class MonsterLevelCondition(EventCondition):
    """
    Compare the level of one particular monster in the player's team.

    The monster is the one whose instance id is stored in a game variable
    (e.g. by ``add_monster`` followed by ``copy_variable``). False when that
    monster is not in the team (for example left in storage).

    Script usage:
        .. code-block::

            is monster_level <variable>,<operator>,<level>

    Script parameters:
        variable: Name of the variable holding the monster's instance id.
        operator: Numeric comparison operator. Accepted values are "less_than",
            "less_or_equal", "greater_than", "greater_or_equal", "equals"
            and "not_equals".
        level: Level to compare with.
    """

    name: ClassVar[str] = "monster_level"
    variable: str
    operator: str
    level: int

    def test(self, session: Session) -> bool:
        iid = session.player.game_variables.get(self.variable)
        for monster in session.player.monsters:
            if monster.instance_id.hex == iid:
                return compare(self.operator, monster.level, int(self.level))
        return False
