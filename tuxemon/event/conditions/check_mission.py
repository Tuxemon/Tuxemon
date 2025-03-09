# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass

from tuxemon.db import MissionStatus
from tuxemon.event import MapCondition, get_npc
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@dataclass
class CheckMissionCondition(EventCondition):
    """
    Check to see the character has failed or completed a mission.
    Check to see if a mission is still pending.

    Script usage:
        .. code-block::

            is check_mission <character>,<method>,<status>

    Script parameters:
        character: Either "player" or npc slug name (e.g. "npc_maple").
        method: Mission or missions.
        "all" means all the existing missions.

    eg. "is check_mission player,mission1,completed"
    eg. "is check_mission player,mission1,pending"
    eg. "is check_mission player,mission1:mission2,completed"
    eg. "is check_mission player,all,completed"

    """

    name = "check_mission"

    def test(self, session: Session, condition: MapCondition) -> bool:
        _character, _mission, _status = condition.parameters[:3]
        character = get_npc(session, _character)
        if character is None:
            logger.error(f"{_character} not found")
            return False
        # status mission
        if _status not in list(MissionStatus):
            logger.error(f"{_status} isn't among {list(MissionStatus)}")
            return False
        # retrieve all missions
        _missions: list[str] = []
        if _mission == "all":
            _missions = [m.slug for m in character.mission_manager.missions]
        else:
            _missions = _mission.split(":")

        if not _missions:
            return False

        result = [
            mission
            for mission in character.mission_manager.missions
            if mission.status == _status and mission.slug in _missions
        ]
        return bool(result)
