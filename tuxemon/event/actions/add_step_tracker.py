# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

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

            add_step_tracker <character>,<tracker_id>,<countdown>[,<milestones>
                            [,<auto_reset>[,<initial_countdown>]]]

    Script parameters:
        character: Either "player" or an NPC slug name (e.g., "npc_maple").
        tracker_id: Unique name for identifying the step tracker.
        countdown: Number of steps before the tracker reaches zero.
        milestones (optional): Step milestones, separated by : (e.g., "500:250:100").
        auto_reset (optional): "true" or "false" to enable or disable automatic reset.
            Defaults to false.
        initial_countdown (optional): Full cycle length. Defaults to countdown value.
    """

    name = "add_step_tracker"
    character: str
    tracker_id: str
    countdown: float
    milestones: str | None = None
    auto_reset: bool | None = None
    initial_countdown: float | None = None

    def start(self, session: Session) -> None:
        character = session.client.get_npc(self.character)
        if character is None:
            logger.error(f"{self.character} not found")
            self.stop()
            return

        steps = round(character.steps)

        milestone_list: list[float] = (
            list(map(float, self.milestones.split(":")))
            if self.milestones
            else []
        )

        resolved_auto_reset = (
            self.auto_reset if self.auto_reset is not None else False
        )
        resolved_initial_countdown = (
            self.initial_countdown
            if self.initial_countdown is not None
            else self.countdown
        )

        step_track = StepTracker(
            steps=steps,
            countdown=self.countdown,
            initial_countdown=resolved_initial_countdown,
            auto_reset=resolved_auto_reset,
            milestones=milestone_list,
        )
        character.step_tracker.add_tracker(self.tracker_id, step_track)

        logger.info(
            f"StepTracker added: Tracker ID: {self.tracker_id}, "
            f"Character: {character.slug}, "
            f"Countdown: {self.countdown}, "
            f"Initial Countdown: {resolved_initial_countdown}, "
            f"Auto Reset: {resolved_auto_reset}, "
            f"Milestones: {milestone_list}"
        )
