# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction


@final
@dataclass
class CallEventAction(EventAction):
    """
    Execute the specified event's actions by name.

    Script usage:
        .. code-block::

            call_event <event_name>

    Script parameters:
        event_name: The name of the event whose actions will be executed.

    """

    name = "call_event"
    event_name: str

    def start(self) -> None:
        event_engine = self.session.client.event_engine
        events = self.session.client.events

        for e in events:
            if e.name == self.event_name:
                event_engine.start_event(e)
