# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from tuxemon.event.eventbus import EventBus

_GLOBAL_EVENT_BUS = EventBus()


def get_event_bus() -> EventBus:
    """
    Returns the global EventBus instance used for dispatching and listening
    to events throughout the application.

    This ensures a centralized event handling mechanism, allowing different
    parts of the system to communicate via published events and registered
    listeners.
    """
    return _GLOBAL_EVENT_BUS
