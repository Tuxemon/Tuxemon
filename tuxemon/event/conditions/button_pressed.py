# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass

from tuxemon.db import SpatialCondition
from tuxemon.event.eventcondition import EventCondition
from tuxemon.platform.const.intentions import constants
from tuxemon.session import Session


@dataclass
class ButtonPressedCondition(EventCondition):
    """
    Check to see if a particular key was pressed.

    Script usage:
        .. code-block::

            is button_pressed <button>

    Script parameters:
        button: A button/intention key (E.g. "INTERACT").
    """

    name = "button_pressed"

    def test(self, session: Session, condition: SpatialCondition) -> bool:
        button = str(condition.parameters[0])

        try:
            button_id = constants[button]
        except KeyError:
            raise ValueError(f"Cannot support key type: {button}")

        # Loop through each event
        for event in session.client.key_events:
            if event.pressed and event.button == button_id:
                return True

        return False
