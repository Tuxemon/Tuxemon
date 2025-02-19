# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging

from tuxemon.platform.const import buttons, events, intentions
from tuxemon.platform.events import PlayerInput

logger = logging.getLogger(__name__)

keymap = {
    buttons.UP: intentions.UP,
    buttons.DOWN: intentions.DOWN,
    buttons.LEFT: intentions.LEFT,
    buttons.RIGHT: intentions.RIGHT,
    buttons.A: intentions.INTERACT,
    buttons.B: intentions.RUN,
    buttons.START: intentions.WORLD_MENU,
    buttons.BACK: intentions.WORLD_MENU,
}


def translate_input_event(event: PlayerInput) -> PlayerInput:
    """
    Translate the given input event into a PlayerInput object.

    Parameters:
        event: The input event to be translated.

    Returns:

    Returns:
        The translated PlayerInput object. If the event cannot be translated,
        the original event is returned.
    """
    try:
        return PlayerInput(keymap[event.button], event.value, event.hold_time)
    except KeyError:
        pass

    unicode_map = {
        "n": intentions.NOCLIP,
        "r": intentions.RELOAD_MAP,
    }

    if event.button == events.UNICODE and event.value in unicode_map:
        return PlayerInput(
            unicode_map[event.value], event.value, event.hold_time
        )

    return event
