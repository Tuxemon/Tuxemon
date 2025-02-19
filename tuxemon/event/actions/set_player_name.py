# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.locale import T

logger = logging.getLogger(__name__)


@final
@dataclass
class SetPlayerNameAction(EventAction):
    """
    Set player name without opening the input screen.

    Script usage:
        .. code-block::

            set_player_name name
            set_player_name name:name

    Script parameters:
        choice: single name or multiple names
        separated by ":" (random choice)
        the names must be in the PO file

    """

    name = "set_player_name"
    choice: str

    def start(self) -> None:
        name: str = ""
        if self.choice.find(":"):
            elements = self.choice.split(":")
            name = random.choice(elements)
        else:
            name = self.choice
        self.session.player.name = T.translate(name)
        logger.info(f"Player name is {T.translate(name)}")
