# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import ClassVar

from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@dataclass
class StepTrackerCondition(EventCondition):
    """
    Evaluates whether a step tracker exists for a character
    and if a milestone has been triggered and not yet marked as shown.

    Script usage:
        .. code-block::

            is step_tracker character,tracker_id,milestone

    Script parameters:
        character: Either "player" or an NPC slug name (e.g., "npc_maple").
        tracker_id: Unique name for identifying the step tracker.
        milestone: Step milestone to check.
    """

    name: ClassVar[str] = "step_tracker"
    character: str
    tracker_id: str
    milestone: float

    def test(self, session: Session) -> bool:
        character = session.client.get_npc(self.character)

        if character is None:
            return False

        tracker = character.step_tracker.get_tracker(self.tracker_id)
        if not tracker:
            return False

        try:
            milestone_value = self.milestone
        except ValueError:
            logger.error(f"Invalid milestone value: '{self.milestone}'")
            return False

        return tracker.has_triggered_milestone(
            milestone_value
        ) and not tracker.has_shown_milestone(milestone_value)
