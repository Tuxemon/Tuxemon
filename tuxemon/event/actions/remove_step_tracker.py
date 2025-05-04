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
class RemoveStepTrackerAction(EventAction):
    """
    Removes a step tracker from a specific character.

    Script usage:
        .. code-block::

            remove_step_tracker <character>,<tracker_id>

    Script parameters:
        character: Either "player" or an NPC slug name (e.g., "npc_maple").
        tracker_id: Unique name for identifying the step tracker.
    """

    name = "remove_step_tracker"
    character: str
    tracker_id: str

    def start(self) -> None:
        character = get_npc(self.session, self.character)
        if character is None:
            logger.error(f"{self.character} not found")
            return

        if not character.step_tracker.get_tracker(self.tracker_id):
            logger.warning(f"StepTracker '{self.tracker_id}' doesn't exist.")
            return

        character.step_tracker.remove_tracker(self.tracker_id)
