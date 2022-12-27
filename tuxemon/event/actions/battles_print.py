# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import datetime as dt
import logging
from dataclasses import dataclass
from typing import Optional, final

from tuxemon.event.eventaction import EventAction

logger = logging.getLogger(__name__)


@final
@dataclass
class BattlesAction(EventAction):
    """
    Print the current value of battle history to the console.

    If no variable is specified, print out values of all battles.

    Script usage:
        .. code-block::

            battles_print
            battles_print [<character>,<result>]

        Script parameters:
            character: Npc slug name (e.g. "npc_maple").
            result: One among "won", "lost" or "draw"

    """

    name = "battles_print"
    character: Optional[str] = None
    result: Optional[str] = None

    def start(self) -> None:
        player = self.session.player
        today = dt.date.today().toordinal()

        if self.character in player.battle_history:
            output, battle_date = player.battle_history[self.character]
            diff_date = today - battle_date
            if self.result == output:
                print(
                    f"{self.result} against {self.character} {diff_date} days ago"
                )
            else:
                print(f"Never {self.result} against {self.character}")
        else:
            print(player.battle_history)
