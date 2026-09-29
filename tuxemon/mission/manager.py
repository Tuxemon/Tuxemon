# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from tuxemon.db import MissionStatus

if TYPE_CHECKING:
    from tuxemon.mission.mission import Mission

logger = logging.getLogger(__name__)


class MissionManager:
    def __init__(self) -> None:
        self.missions: dict[str, Mission] = {}

    def assign_mission_to(self, mission: Mission, npc_slug: str) -> None:
        mission.assigned_to = npc_slug
        self.add_mission(mission)

    def add_mission(self, mission: Mission) -> None:
        if mission.slug not in self.missions:
            self.missions[mission.slug] = mission

    def remove_mission(self, mission: Mission) -> None:
        self.missions.pop(mission.slug, None)

    def remove_by_slug(self, slug: str) -> None:
        self.missions.pop(slug, None)

    def find_mission(self, slug: str) -> Mission | None:
        return self.missions.get(slug)

    def get_mission_count(self) -> int:
        return len(self.missions)

    def get_active_missions(self) -> list[Mission]:
        return [m for m in self.missions.values() if m.is_active()]

    def get_completed_missions(self) -> list[Mission]:
        return [m for m in self.missions.values() if m.is_completed()]

    def get_missions_by_status(self, status: MissionStatus) -> list[Mission]:
        return [m for m in self.missions.values() if m.status == status]

    def get_missions_for(self, npc_slug: str) -> list[Mission]:
        return [
            m
            for m in self.missions.values()
            if m.assigned_to in (None, npc_slug)
            and m.status != MissionStatus.REMOVED
        ]
