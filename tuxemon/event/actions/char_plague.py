# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, final

from tuxemon.db import PlagueType
from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction

logger = logging.getLogger(__name__)


@final
@dataclass
class CharPlagueAction(EventAction):
    """
    Set the character as infected, inoculated or healthy.

    Script usage:
        .. code-block::

            char_plague <value>[,character]

    Script parameters:
        condition: Infected, inoculated or healthy
        character: Either "player" or character slug name (e.g. "npc_maple").

    """

    name = "char_plague"
    value: str
    character: Optional[str] = None

    def start(self) -> None:
        self.character = "player" if self.character is None else self.character
        character = get_npc(self.session, self.character)
        if character is None:
            logger.error(f"{self.character} not found")
            return
        if self.value == PlagueType.infected:
            character.plague = PlagueType.infected
        elif self.value == PlagueType.healthy:
            character.plague = PlagueType.healthy
        elif self.value == PlagueType.inoculated:
            character.plague = PlagueType.inoculated
        else:
            raise ValueError(
                f"{self.value} must be infected, inoculated or healthy."
            )
