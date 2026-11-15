# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.constants.paths import USER_RECORDING_DIR
from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@final
@dataclass
class InputLoadAction(EventAction):
    """
    Load a recording from a file into memory under a given name.

    Script usage:
        .. code-block::

            input_load <filepath> <name>
    """

    name = "input_load"
    filepath: str
    recording_name: str

    def start(self, session: Session) -> None:
        recorder = session.client.input_recorder
        bus = session.client.event_bus

        filepath = USER_RECORDING_DIR / self.filepath
        if filepath.suffix == "":
            filepath = filepath.with_suffix(".json")

        events = recorder.load_from_file(filepath, name=self.recording_name)
        if events:
            bus.publish(
                "input.loaded",
                filepath=filepath.as_posix(),
                name=self.recording_name,
                events=events,
            )
        else:
            bus.publish(
                "input.load_failed",
                filepath=filepath.as_posix(),
                name=self.recording_name,
            )
