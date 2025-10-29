# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass

from tuxemon.event import MapCondition, get_npc
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

    name = "step_tracker"

    def test(self, session: Session, condition: MapCondition) -> bool:
        _character, tracker_id, milestone = condition.parameters
        character = get_npc(session, _character)

        if character is None:
            return False

        tracker = character.step_tracker.get_tracker(tracker_id)
        if not tracker:
            return False

        try:
            milestone_value = float(milestone)
        except ValueError:
            logger.error(f"Invalid milestone value: '{milestone}'")
            return False

        return tracker.has_triggered_milestone(
            milestone_value
        ) and not tracker.has_shown_milestone(milestone_value)
