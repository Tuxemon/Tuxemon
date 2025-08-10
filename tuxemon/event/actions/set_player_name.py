# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.locale import T
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@final
@dataclass
class SetPlayerNameAction(EventAction):
    """
    Set player name without opening the input screen.

    Script usage:
        .. code-block::

            set_player_name name
            set_player_name name1:name2

    Script parameters:
        choice: A single name or multiple names separated by ":".
            If multiple, one will be randomly selected.
    """

    name = "set_player_name"
    choice: str

    def start(self, session: Session) -> None:
        if ":" in self.choice:
            elements = self.choice.split(":")
            selected_name = random.choice(elements)
        else:
            selected_name = self.choice

        session.player.name = T.translate(selected_name)
        logger.info(f"Player name is {session.player.name}")
