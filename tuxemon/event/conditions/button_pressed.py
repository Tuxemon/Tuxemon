# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

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

    name: ClassVar[str] = "button_pressed"
    button: str

    def test(self, session: Session) -> bool:
        try:
            button_id = constants[self.button]
        except KeyError:
            raise ValueError(f"Cannot support key type: {self.button}")

        return session.client.input_cache.was_button_pressed(button_id)
