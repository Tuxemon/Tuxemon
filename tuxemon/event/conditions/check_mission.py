# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import ClassVar

from tuxemon.db import MissionStatus
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@dataclass
class CheckMissionCondition(EventCondition):
    """
    Check mission status for one or more missions.

    Script usage:
        .. code-block::

            is check_mission <character>,<method>,<status>[,<mode>]

    Parameters:
        character: Either "player" or NPC slug (e.g. "npc_maple")
        method: Mission slug(s), colon-separated (e.g. "mission1:mission2") or "all"
        status: One of ["pending", "completed", "failed"]
        mode (optional): "any" (default) or "all"
            "any" returns True if at least one mission matches status
            "all" returns True only if all listed missions match status

    Examples:
        - "is check_mission player,mission1,completed"
        - "is check_mission player,mission1:mission2,completed,all"
        - "is check_mission player,all,pending"
        - "is check_mission npc_maple,missionA:missionB,failed,any"
    """

    name: ClassVar[str] = "check_mission"
    character: str
    mission: str
    status: str
    mode: str | None = None

    def test(self, session: Session) -> bool:
        _mode = self.mode if self.mode else "any"

        character = session.client.get_npc(self.character)
        if character is None:
            logger.error(f"Character '{self.character}' not found.")
            return False

        if self.status not in MissionStatus.__members__:
            logger.error(f"'{self.status}' isn't a valid MissionStatus.")
            return False
        target_status = MissionStatus[self.status]

        if self.mission == "all":
            missions = character.mission_controller.get_missions()
        else:
            mission_slugs = self.mission.split(":")
            missions = [
                m
                for m in character.mission_controller.get_missions()
                if m.slug in mission_slugs
            ]

        if not missions:
            logger.info("No missions matched the criteria.")
            return False

        if _mode == "all":
            return all(m.status == target_status for m in missions)
        return any(m.status == target_status for m in missions)
