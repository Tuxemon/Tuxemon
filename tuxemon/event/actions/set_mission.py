# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, final

from tuxemon.db import MissionStatus
from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.mission import Mission
from tuxemon.npc import NPC


@final
@dataclass
class SetMissionAction(EventAction):
    """
    Set mission.

    Script usage:
        .. code-block::

            set_mission <slug>,<operation>[,status][,trainer_slug]

    Script parameters:
        slug: slug mission
        operation: add, remove or change
        status: completed, pending,failed (default pending)
        trainer_slug: slug name (e.g. "npc_maple"), default player.

    """

    name = "set_mission"
    slug: str
    operation: str
    status: MissionStatus = MissionStatus.pending
    trainer_slug: Optional[str] = None

    def start(self) -> None:
        player = self.session.player
        trainer: Optional[NPC]
        if self.trainer_slug is None:
            trainer = player
        else:
            trainer = get_npc(self.session, self.trainer_slug)

        assert trainer, "No Trainer found with slug '{}'".format(
            self.trainer_slug or "player"
        )

        mission = Mission()
        mission.load(self.slug)
        mission.status = self.status
        existing = trainer.find_mission(self.slug)
        if self.operation == "add" and existing is None:
            trainer.add_mission(mission)
        if self.operation == "remove" and existing:
            trainer.remove_mission(existing)
        if self.operation == "change" and existing:
            existing.status = self.status
