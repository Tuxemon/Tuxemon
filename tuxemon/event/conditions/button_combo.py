# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from tuxemon.event import MapCondition
from tuxemon.event.eventcondition import EventCondition
from tuxemon.platform.const.intentions import constants
from tuxemon.session import Session


class ButtonComboCondition(EventCondition):
    """
    Check to see if a particular sequence of buttons was pressed.

    Script usage:
        .. code-block::

            is button_combo <buttons>

    Script parameters:
        buttons: A sequence of button/intention keys (E.g. "up:down:interact").
    """

    name = "button_combo"

    def test(self, session: Session, condition: MapCondition) -> bool:
        _buttons = condition.parameters[0].split(":")
        ids: list[int] = []
        for _button in _buttons:
            try:
                button = constants[_button.upper()]
            except KeyError:
                raise ValueError("Constant not found")
            ids.append(button)
        return session.client.input_manager.input_history.is_button_combo(ids)
