# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Optional, final

from tuxemon.event.eventaction import EventAction


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

        for battle in player.battles:
            if battle.opponent == self.character:
                total = sum(
                    1
                    for battle in player.battles
                    if battle.opponent == self.character
                )
                diff_date = today - battle.date
                if self.result == battle.outcome:
                    print(
                        f"You {self.result} {total} times against {self.character}\n"
                        f"{diff_date} days ago"
                    )
                else:
                    print(f"Never {self.result} against {self.character}")
            else:
                print(battle.opponent, battle.outcome, battle.date)
