# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.db import MissionStatus
from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.mission import Mission

logger = logging.getLogger(__name__)


@final
@dataclass
class SetMissionAction(EventAction):
    """
    Set mission.

    Script usage:
        .. code-block::

            set_mission <character>,<operation>[,status]

    Script parameters:
        character: Either "player" or npc slug name (e.g. "npc_maple").
        slug: slug mission
        operation: add, remove or change
        status: completed, pending, failed (default pending)

    """

    name = "set_mission"
    character: str
    slug: str
    operation: str
    status: MissionStatus = MissionStatus.pending

    def start(self) -> None:
        character = get_npc(self.session, self.character)
        if character is None:
            logger.error(f"{self.character} not found")
            return

        mission = Mission()
        mission.load(self.slug)
        mission.status = self.status
        existing = character.find_mission(self.slug)
        if self.operation == "add" and existing is None:
            character.add_mission(mission)
        if self.operation == "remove" and existing:
            character.remove_mission(existing)
        if self.operation == "change" and existing:
            existing.status = self.status
