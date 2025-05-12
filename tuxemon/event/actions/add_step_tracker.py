# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, final

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session
from tuxemon.step_tracker import StepTracker

logger = logging.getLogger(__name__)


@final
@dataclass
class AddStepTrackerAction(EventAction):
    """
    Adds a step tracker to a specific character.

    Script usage:
        .. code-block::

            add_step_tracker <character>,<tracker_id>,<countdown>,[,milestones]

    Script parameters:
        character: Either "player" or an NPC slug name (e.g., "npc_maple").
        tracker_id: Unique name for identifying the step tracker.
        countdown: Number of steps before the tracker reaches zero.
        milestones (optional): Step milestones, separated by : (e.g., "500:250:100").
    """

    name = "add_step_tracker"
    character: str
    tracker_id: str
    countdown: float
    milestones: Optional[str] = None

    def start(self, session: Session) -> None:
        character = get_npc(session, self.character)
        if character is None:
            logger.error(f"{self.character} not found")
            return

        steps = round(character.steps)
        milestones: list[float] = (
            list(map(float, self.milestones.split(":")))
            if self.milestones
            else []
        )

        step_track = StepTracker(
            steps=steps, countdown=self.countdown, milestones=milestones
        )
        character.step_tracker.add_tracker(self.tracker_id, step_track)

        logger.info(
            f"StepTracker:",
            f"Tracker ID: {self.tracker_id}, "
            f"Character:{character.slug}, "
            f"Countdown: {self.countdown}, "
            f"Milestones: {milestones}",
        )
