# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import final

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction


@final
@dataclass
class CharSpeedAction(EventAction):
    """
    Set the character movement speed to a custom value.

    Script usage:
        .. code-block::

            char_speed <character>,<speed>

    Script parameters:
        character: Either "player" or character slug name (e.g. "npc_maple").
        speed: Speed amount.

    """

    name = "char_speed"
    character: str
    speed: float

    def start(self) -> None:
        character = get_npc(self.session, self.character)
        assert character
        character.moverate = self.speed
        # Just set some sane limit to avoid losing sprites
        assert 0 < character.moverate < 20
