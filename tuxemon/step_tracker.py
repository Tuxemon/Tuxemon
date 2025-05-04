# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class MilestoneStatus:
    triggered: bool = False
    shown: bool = False


@dataclass
class StepTracker:
    steps: float = 0.0
    countdown: float = 100.0
    milestones: list[float] = field(
        default_factory=lambda: [500, 250, 100, 50]
    )
    milestone_status: dict[float, MilestoneStatus] = field(
        default_factory=dict
    )

    def get_state(self) -> dict[str, Any]:
        """Retrieve the current state of the step tracker."""
        return {
            "steps": self.steps,
            "countdown": self.countdown,
            "milestones": self.milestones,
            "milestone_status": self.milestone_status,
        }

    def update_steps(self, diff_x: float, diff_y: float) -> None:
        movement = diff_x + diff_y
        self.steps += movement
        self.countdown = max(0, self.countdown - movement)
        self.check_milestone_events()

    def check_milestone_events(self) -> Optional[float]:
        triggered_milestone: Optional[float] = None
        if self.milestones:
            for milestone in self.milestones:
                if (
                    self.countdown <= milestone
                    and milestone not in self.milestone_status
                ):
                    self.trigger_milestone_event(milestone)
                    triggered_milestone = milestone
        return triggered_milestone

    def trigger_milestone_event(self, milestone: float) -> None:
        if milestone not in self.milestone_status:
            self.milestone_status[milestone] = MilestoneStatus(triggered=True)

    def show_milestone_dialogue(self, milestone: float) -> None:
        if milestone in self.milestone_status:
            self.milestone_status[milestone].shown = True

    def has_triggered_milestone(self, milestone: float) -> bool:
        return (
            milestone in self.milestone_status
            and self.milestone_status[milestone].triggered
        )

    def has_shown_milestone(self, milestone: float) -> bool:
        return (
            milestone in self.milestone_status
            and self.milestone_status[milestone].shown
        )

    def has_reached_milestone(self, milestone: float) -> bool:
        return self.countdown <= milestone


class StepTrackerManager:
    def __init__(self) -> None:
        self.trackers: dict[str, StepTracker] = {}
        self.global_event_triggered = False

    def update_all(self, diff_x: float, diff_y: float) -> None:
        for tracker in self.trackers.values():
            tracker.update_steps(diff_x, diff_y)

    def add_tracker(self, tracker_id: str, tracker: StepTracker) -> None:
        if tracker_id in self.trackers:
            logger.error(f"StepTracker ID '{tracker_id}' already exists.")
        else:
            self.trackers[tracker_id] = tracker

    def remove_tracker(self, tracker_id: str) -> None:
        if tracker_id in self.trackers:
            del self.trackers[tracker_id]
            logger.info(f"StepTracker ID '{tracker_id}' has been removed.")
        else:
            logger.error(f"StepTracker ID '{tracker_id}' does not exist.")

    def get_tracker(self, tracker_id: str) -> Optional[StepTracker]:
        if tracker_id in self.trackers:
            return self.trackers[tracker_id]
        else:
            return None


def decode_steps(json_data: Mapping[str, Any]) -> StepTrackerManager:
    tracking_data = StepTrackerManager()
    if json_data:
        tracking_data.trackers = {
            key: StepTracker(
                steps=value["steps"],
                countdown=value["countdown"],
                milestones=value["milestones"],
                milestone_status={
                    float(m): MilestoneStatus(**status)
                    for m, status in value["milestone_status"].items()
                },
            )
            for key, value in json_data.items()
        }
    else:
        tracking_data.trackers = {}
    return tracking_data


def encode_steps(step_data: StepTrackerManager) -> Mapping[str, Any]:
    return {
        tracker: {
            **data.get_state(),
            "milestone_status": {
                str(m): data.milestone_status[m].__dict__
                for m in data.milestone_status
            },
        }
        for tracker, data in step_data.trackers.items()
    }
