# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from tuxemon.event import MapCondition
from tuxemon.event.conditions.player_at import PlayerAtCondition
from tuxemon.event.conditions.player_facing import PlayerFacingCondition
from tuxemon.event.conditions.to_talk import ToTalkCondition
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session


class BehaviorCondition(EventCondition):
    """
    Check if the behavior's conditions are true.

    Behavior is a combination of 1 action with 1 or more conditions.

    """

    name = "behav"

    def test(self, session: Session, condition: MapCondition) -> bool:
        cond = condition
        param = condition.parameters
        if param[0] == "talk":
            to_talk = ToTalkCondition().test(
                session,
                MapCondition(
                    "to_talk",
                    [param[1]],
                    cond.x,
                    cond.y,
                    cond.width,
                    cond.height,
                    "is",
                    "cond10",
                ),
            )
            return to_talk
        elif param[0] == "door":
            player_at = PlayerAtCondition().test(
                session,
                MapCondition(
                    "player_at",
                    [],
                    cond.x,
                    cond.y,
                    cond.width,
                    cond.height,
                    "is",
                    "cond10",
                ),
            )
            player_facing = PlayerFacingCondition().test(
                session,
                MapCondition(
                    "player_facing",
                    [param[1]],
                    cond.x,
                    cond.y,
                    cond.width,
                    cond.height,
                    "is",
                    "cond20",
                ),
            )
            return player_at and player_facing
        return False
