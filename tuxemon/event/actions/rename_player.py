# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, final

from tuxemon import prepare
from tuxemon.event.eventaction import EventAction
from tuxemon.locale import T
from tuxemon.session import Session


@final
@dataclass
class RenamePlayerAction(EventAction):
    """
    Open the text input screen to rename the player.

    Script usage:
        .. code-block::

            rename_player [random]

    Script parameters:
        random: Adding "random" makes appear the
        dontcare button in the input.
    """

    name = "rename_player"
    random: Optional[str] = None

    def set_player_name(self, name: str) -> None:
        client = self.client
        client.event_engine.execute_action("set_player_name", [name], True)

    def start(self, session: Session) -> None:
        self.client = session.client
        session.client.push_state(
            "InputMenu",
            prompt=T.translate("input_name"),
            callback=self.set_player_name,
            escape_key_exits=False,
            initial=session.player.name,
            char_limit=prepare.PLAYER_NAME_LIMIT,
            random=bool(self.random),
        )

    def update(self, session: Session) -> None:
        try:
            session.client.get_state_by_name("InputMenu")
        except ValueError:
            self.stop()
