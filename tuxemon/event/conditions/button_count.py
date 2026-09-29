# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from typing import ClassVar

from tuxemon.event.eventcondition import EventCondition
from tuxemon.platform.const.intentions import constants
from tuxemon.session import Session
from tuxemon.tools import compare


class ButtonCountCondition(EventCondition):
    """
    Check to see how many time a particular button was pressed.

    Script usage:
        .. code-block::

            is button_count <button>,<operator>,<amount>

    Script parameters:
        button: A button/intention key (E.g. "up").
        operator: Numeric comparison operator. Accepted values are "less_than",
            "less_or_equal", "greater_than", "greater_or_equal", "equals"
            and "not_equals".
        amount: The number of times the button was pressed.
    """

    name: ClassVar[str] = "button_count"
    button_id: str
    operator: str
    amount: int

    def test(self, session: Session) -> bool:
        try:
            button = constants[self.button_id.upper()]
        except KeyError:
            raise ValueError("Constant not found")
        counter = (
            session.client.input_manager.input_history.count_button_clicks()
        )
        output = counter.get(button, 0)
        return compare(self.operator, output, self.amount)
