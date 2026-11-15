# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@final
@dataclass
class AFKThresholdAction(EventAction):
    """
    Add, modify, or remove AFK thresholds.

    Script usage:
        .. code-block::

            afk_threshold <action> <level> [duration]

    Script parameters:
        action: One of "add", "modify", "remove"
        level: The threshold name (string)
        duration: Required for "add" and "modify" (float, seconds)
    """

    name = "afk_threshold"
    action: str
    level: str
    duration: float | None = None

    def start(self, session: Session) -> None:
        afk = session.client.afk_manager
        bus = session.client.event_bus

        if self.action == "add":
            if self.duration is None:
                logger.error("Add threshold requires a duration")
                self.stop()
                return
            afk.add_threshold(self.level, self.duration)
            logger.info(
                f"Added AFK threshold {self.level} at {self.duration}s"
            )
            bus.publish(
                "afk.threshold_added", level=self.level, duration=self.duration
            )

        elif self.action == "modify":
            if self.duration is None:
                logger.error("Modify threshold requires a duration")
                self.stop()
                return
            success = afk.modify_threshold(self.level, self.duration)
            if success:
                logger.info(
                    f"Modified AFK threshold {self.level} to {self.duration}s"
                )
                bus.publish(
                    "afk.threshold_modified",
                    level=self.level,
                    duration=self.duration,
                )
            else:
                logger.warning(f"Threshold {self.level} not found to modify")

        elif self.action == "remove":
            success = afk.remove_threshold(self.level)
            if success:
                logger.info(f"Removed AFK threshold {self.level}")
                bus.publish("afk.threshold_removed", level=self.level)
            else:
                logger.warning(f"Threshold {self.level} not found to remove")

        else:
            logger.error(f"Unknown threshold action: {self.action}")
