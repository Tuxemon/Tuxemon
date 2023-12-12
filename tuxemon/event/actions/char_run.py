# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import final

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction


@final
@dataclass
class CharRunAction(EventAction):
    """
    Set the character movement speed to the global run speed.

    Script usage:
        .. code-block::

            char_run <character>

    Script parameters:
        character: Either "player" or character slug name (e.g. "npc_maple").

    """

    name = "char_run"
    character: str

    def start(self) -> None:
        character = get_npc(self.session, self.character)
        assert character
        character.moverate = self.session.client.config.player_runrate
