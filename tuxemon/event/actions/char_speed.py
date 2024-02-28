# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.prepare import MOVERATE_RANGE

logger = logging.getLogger(__name__)


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
        if character is None:
            logger.error(f"{self.character} not found")
            return
        if MOVERATE_RANGE[0] < self.speed < MOVERATE_RANGE[1]:
            logger.info(f"{character.name}'s moverate is {self.speed}")
            character.moverate = self.speed
        else:
            raise ValueError(f"{self.speed} isn't among {MOVERATE_RANGE}")
