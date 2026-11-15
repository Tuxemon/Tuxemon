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
class InputRecordAction(EventAction):
    """
    Start or stop input recording, optionally naming the recording.

    Script usage:
        .. code-block::

            input_record <action> [name]
    """

    name = "input_record"
    action: str
    recording_name: str | None = None

    def start(self, session: Session) -> None:
        recorder = session.client.input_recorder
        bus = session.client.event_bus

        if self.action == "start":
            recorder.start_recording(session)
            bus.publish("input.record_started", name=self.recording_name)
            logger.info(f"Recording started (name={self.recording_name})")
        elif self.action == "stop":
            events = recorder.stop_recording(name=self.recording_name)
            bus.publish(
                "input.record_stopped", name=self.recording_name, events=events
            )
            logger.info(
                f"Recording stopped (name={self.recording_name}, {len(events)} events)"
            )
        else:
            logger.error(f"Unknown input_record action: {self.action}")
