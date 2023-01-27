# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.prepare import PLAYER_NAME_LIMIT


@final
@dataclass
class SetPlayerNameAction(EventAction):
    """
    Set the player name without opening the input.

    Script usage:
        .. code-block::

            set_player_name <name>

    """

    name = "set_player_name"
    name: str

    def start(self) -> None:
        player = self.session.player
        if len(self.name) <= PLAYER_NAME_LIMIT:
            player.name = self.name
        else:
            raise ValueError(
                f"{self.name} too long (max {PLAYER_NAME_LIMIT} characters)",
            )
