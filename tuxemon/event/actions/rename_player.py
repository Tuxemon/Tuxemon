# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import final

from tuxemon import prepare
from tuxemon.event.eventaction import EventAction
from tuxemon.locale import T
from tuxemon.menu.input import InputMenu


@final
@dataclass
class RenamePlayerAction(EventAction):
    """
    Open the text input screen to rename the player.

    Script usage:
        .. code-block::

            rename_player

    """

    name = "rename_player"

    def set_player_name(self, name: str) -> None:
        self.session.player.name = name

    def start(self) -> None:
        self.session.client.push_state(
            InputMenu(
                prompt=T.translate("input_name"),
                callback=self.set_player_name,
                escape_key_exits=False,
                initial=self.session.player.name,
                char_limit=prepare.PLAYER_NAME_LIMIT,
            )
        )

    def update(self) -> None:
        try:
            self.session.client.get_state_by_name(InputMenu)
        except ValueError:
            self.stop()
