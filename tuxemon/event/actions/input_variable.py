# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, final

from tuxemon.event.eventaction import EventAction
from tuxemon.locale.locale import T
from tuxemon.tools import parse_flag

if TYPE_CHECKING:
    from tuxemon.session import Session


@final
@dataclass
class InputVariableAction(EventAction):
    """
    Set a code and check if it's correct or not.
    The player's output will be by default lowercase.

    Script usage:

        .. code-block:: text

           input_variable <variable>,<question>[,answer][,escape]

    Script parameters:

        question:
            The question the player needs to reply (e.g. "access_code").
            Then you create the msgid "access_code" inside the PO file:

                msgid "access_code"
                msgstr "Here the actual question?"

        variable:
            Name of the variable where to store the output.

        escape:
            Optional string flag ("true", "1", "yes" for True),
            defaults to False when omitted.

    Examples:

        "input_variable access_code,response_question"
        "input_variable access_code,response_question,escape"

        -> "is variable_set response_question:whatswrittenbytheplayer"
        -> "not variable_set response_question:whatswrittenbytheplayer"
    """

    name = "input_variable"
    question: str
    variable: str
    escape: str | None = None

    def check_setcode(self, name: str) -> None:
        client = self.client.event_engine
        var = f"{self.variable}:{name.lower()}"
        client.execute_action("set_variable", [var], True)

    def start(self, session: Session) -> None:
        self.client = session.client
        _escape = parse_flag(self.escape)
        session.client.push_state(
            "InputMenu",
            prompt=T.translate(self.question),
            callback=self.check_setcode,
            escape_key_exits=_escape,
        )

    def update(self, session: Session, dt: float) -> None:
        if "InputMenu" not in session.client.active_state_names:
            self.stop()
