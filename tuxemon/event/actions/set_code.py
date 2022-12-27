# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.locale import T
from tuxemon.menu.input import InputMenu


@final
@dataclass
class SetCodeAction(EventAction):
    """
    Set a code and checks if it's correct or not.
    Case Sensitive:
    ATTENTION and AtTenTION are two different words.

    Script usage:
        .. code-block::

            set_code <question>,<answer>,<variable>

    Script parameters:
        question: The question the player needs to reply.
                  (eg. "access_code")
                  then you create the msgid "access_code"
                  inside the English PO file, as follows:
                  msgid "access_code"
                  msgstr "Here the actual question?"
        answer: The right answer to the question.
        variable: Where the result (right/wrong) is saved.

    """

    name = "set_code"
    question: str
    answer: str
    variable: str

    def check_setcode(self, name: str) -> None:
        player = self.session.player
        if self.answer == name:
            player.game_variables[self.variable] = "right"
        else:
            player.game_variables[self.variable] = "wrong"

    def start(self) -> None:
        self.session.client.push_state(
            state_name=InputMenu,
            prompt=T.translate(self.question),
            callback=self.check_setcode,
            escape_key_exits=False,
            char_limit=len(self.answer),
        )

    def update(self) -> None:
        try:
            self.session.client.get_state_by_name(InputMenu)
        except ValueError:
            self.stop()
