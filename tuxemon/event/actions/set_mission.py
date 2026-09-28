# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.db import MissionStatus
from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@final
@dataclass
class SetMissionAction(EventAction):
    """
    Set missions by updating it and by checking the prerequisites.

    Script usage:
        .. code-block::

            set_mission <character>

    Script parameters:
        character: Either "player" or npc slug name (e.g. "npc_maple").
    """

    name = "set_mission"
    character: str

    def start(self, session: Session) -> None:
        character = session.client.get_npc(self.character)
        if character is None:
            logger.error(f"Character '{self.character}' not found.")
            self.stop()
            return

        missions = (
            character.mission_controller.get_missions_with_met_prerequisites()
        )
        if not missions:
            logger.info(f"No missions met prerequisites for {self.character}.")
            self.stop()
            return

        for mission in missions:
            if mission.assigned_to not in (None, character.slug):
                continue

            if mission.assigned_to is None:
                character.mission_controller.assign_mission(mission)

            mission.check_step_conditions(character)

            progress = mission.get_progress()
            if progress >= 100.0:
                mission.update_status(MissionStatus.COMPLETED)
                if mission.repeatable:
                    mission.completed_steps.clear()
                    mission.update_status(MissionStatus.PENDING)
