# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.platform.const.sizes import MOVERATE_RANGE
from tuxemon.session import Session

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

    def start(self, session: Session) -> None:
        character = session.client.get_npc(self.character)
        if character is None:
            logger.error(f"{self.character} not found")
            self.stop()
            return
        if MOVERATE_RANGE[0] < self.speed < MOVERATE_RANGE[1]:
            logger.info(f"{character.name}'s moverate is {self.speed}")
            character.set_moverate(self.speed)
        else:
            raise ValueError(f"{self.speed} isn't among {MOVERATE_RANGE}")
