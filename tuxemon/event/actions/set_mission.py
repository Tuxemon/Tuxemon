# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction

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

    def start(self) -> None:
        character = get_npc(self.session, self.character)
        if character is None:
            logger.error(f"{self.character} not found")
            return

        missions = (
            character.mission_manager.get_missions_with_met_prerequisites()
        )
        if not missions:
            return
        else:
            character.mission_manager.update_mission_progress()
