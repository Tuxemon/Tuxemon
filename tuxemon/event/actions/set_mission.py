# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, final

from tuxemon.db import MissionStatus
from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.mission import Mission


@final
@dataclass
class SetMissionAction(EventAction):
    """
    Set mission.

    Script usage:
        .. code-block::

            set_mission <slug>,<operation>[,status][,npc_slug]

    Script parameters:
        slug: slug mission
        operation: add, remove or change
        status: completed, pending, failed (default pending)
        npc_slug: slug name (e.g. "npc_maple"), default player.

    """

    name = "set_mission"
    slug: str
    operation: str
    status: MissionStatus = MissionStatus.pending
    npc_slug: Optional[str] = None

    def start(self) -> None:
        self.npc_slug = "player" if self.npc_slug is None else self.npc_slug
        npc = get_npc(self.session, self.npc_slug)
        assert npc

        mission = Mission()
        mission.load(self.slug)
        mission.status = self.status
        existing = npc.find_mission(self.slug)
        if self.operation == "add" and existing is None:
            npc.add_mission(mission)
        if self.operation == "remove" and existing:
            npc.remove_mission(existing)
        if self.operation == "change" and existing:
            existing.status = self.status
