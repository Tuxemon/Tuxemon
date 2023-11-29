# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from tuxemon.db import MissionStatus
from tuxemon.event import MapCondition
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session


class CheckMissionCondition(EventCondition):
    """
    Check to see the player has failed or completed a mission.
    Check to see if a mission is still pending.

    Script usage:
        .. code-block::

            is check_mission <method>,<status>

    Script parameters:
        method: Mission or missions.
        "all" means all the existing missions.

    eg. "is check_mission mission1,completed"
    eg. "is check_mission mission1,pending"
    eg. "is check_mission mission1:mission2,completed"
    eg. "is check_mission all,completed"

    """

    name = "check_mission"

    def test(self, session: Session, condition: MapCondition) -> bool:
        player = session.player

        self.mission = condition.parameters[0]
        self.status = MissionStatus(condition.parameters[1])

        _missions: list[str] = []
        if self.mission == "all":
            _missions = [m.slug for m in player.missions]
        else:
            _missions = self.mission.split(":")

        if not _missions:
            return False

        _total = len(_missions)

        for mission in player.missions:
            if mission.status != self.status and _missions:
                _missions.remove(mission.slug)

        return len(_missions) == _total
