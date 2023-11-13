# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from tuxemon.event import MapCondition
from tuxemon.event.conditions.player_at import PlayerAtCondition as PAt
from tuxemon.event.conditions.player_facing import (
    PlayerFacingCondition as PFacing,
)
from tuxemon.event.conditions.to_talk import ToTalkCondition as ToTalk
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session


class BehaviorCondition(EventCondition):
    """
    Check if the behaviors conditions are correct.

    """

    name = "behav"

    def test(self, session: Session, condition: MapCondition) -> bool:
        cond = condition
        param = condition.parameters
        if param[0] == "talk":
            to_talk = ToTalk().test(
                session,
                MapCondition(
                    "to_talk",
                    [param[1]],
                    0,
                    0,
                    0,
                    0,
                    "is",
                    "",
                ),
            )
            return to_talk
        elif param[0] == "door":
            player_at = PAt().test(
                session,
                MapCondition(
                    "player_at",
                    [],
                    cond.x,
                    cond.y,
                    cond.width,
                    cond.height,
                    "is",
                    "",
                ),
            )
            player_facing = PFacing().test(
                session,
                MapCondition(
                    "player_facing",
                    [param[1]],
                    cond.x,
                    cond.y,
                    cond.width,
                    cond.height,
                    "is",
                    None,
                ),
            )
            return player_at and player_facing
        return False
