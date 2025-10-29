# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@final
@dataclass
class SetStepTrackerMilestoneShownAction(EventAction):
    """
    Marks a milestone on a step tracker as shown for a specific character.

    Script usage:
        .. code-block::

            set_step_tracker_milestone_shown <character>,<tracker_id>,<milestone>

    Script parameters:
        character: Either "player" or an NPC slug name (e.g., "npc_maple").
        tracker_id: Unique name for identifying the step tracker.
        milestone: Step milestone to mark as shown.
    """

    name = "set_step_tracker_milestone_shown"
    character: str
    tracker_id: str
    milestone: float

    def start(self, session: Session) -> None:
        character = get_npc(session, self.character)
        if character is None:
            logger.error(f"Character '{self.character}' not found.")
            return

        tracker = character.step_tracker.get_tracker(self.tracker_id)
        if not tracker:
            logger.warning(
                f"StepTracker '{self.tracker_id}' not found for character '{self.character}'."
            )
            return

        if tracker.has_shown_milestone(self.milestone):
            logger.info(
                f"Milestone {self.milestone} already marked as shown for '{self.character}'."
            )
            return

        tracker.show_milestone_dialogue(self.milestone)
        logger.info(
            f"Milestone {self.milestone} on tracker '{self.tracker_id}' for '{self.character}' marked as shown."
        )
