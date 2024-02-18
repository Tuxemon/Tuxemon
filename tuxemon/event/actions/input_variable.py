# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, final

from tuxemon.event.eventaction import EventAction
from tuxemon.locale import T
from tuxemon.menu.input import InputMenu


@final
@dataclass
class InputVariableAction(EventAction):
    """
    Set a code and checks if it's correct or not.
    The player's output will be by default lowercase.

    Script usage:
        .. code-block::

            input_variable <variable>,<question>[,answer][,escape]

    Script parameters:
        question: The question the player needs to reply (eg. "access_code")
                  then you create the msgid "access_code" inside the PO file:
                  msgid "access_code"
                  msgstr "Here the actual question?"
        variable: Name of the variable where to store the output.
        escape: Whether the input can be closed or not. Default False.

    eg. "input_variable access_code,response_question"
    eg. "input_variable access_code,response_question,escape"

    -> "is variable_set response_question:whatswrittenbytheplayer"
    -> "not variable_set response_question:whatswrittenbytheplayer"

    """

    name = "input_variable"
    question: str
    variable: str
    escape: Optional[str] = None

    def check_setcode(self, name: str) -> None:
        client = self.session.client.event_engine
        var = f"{self.variable}:{name.lower()}"
        client.execute_action("set_variable", [var], True)

    def start(self) -> None:
        _escape = True if self.escape else False
        self.session.client.push_state(
            InputMenu(
                prompt=T.translate(self.question),
                callback=self.check_setcode,
                escape_key_exits=_escape,
            )
        )

    def update(self) -> None:
        try:
            self.session.client.get_state_by_name(InputMenu)
        except ValueError:
            self.stop()
