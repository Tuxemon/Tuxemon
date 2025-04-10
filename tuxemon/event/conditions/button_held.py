# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from tuxemon.event import MapCondition
from tuxemon.event.eventcondition import EventCondition
from tuxemon.platform.const.intentions import constants
from tuxemon.session import Session


class ButtonHeldCondition(EventCondition):
    """
    Check to see if a particular key was held for a certain number of frames.

    Script usage:
        .. code-block::

            is button_held <button>,<frames>

    Script parameters:
        button: A button/intention key (E.g. "up").
        frames: The number of frames the button must be held.
    """

    name = "button_held"

    def test(self, session: Session, condition: MapCondition) -> bool:
        button_id, time_ms = condition.parameters[:2]
        try:
            button = constants[button_id.upper()]
        except KeyError:
            raise ValueError("Constant not found")
        return session.client.input_manager.input_history.is_button_held_down(
            button, int(time_ms)
        )
