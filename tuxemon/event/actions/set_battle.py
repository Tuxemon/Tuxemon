# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import datetime as dt
import logging
from dataclasses import dataclass
from typing import final

from tuxemon.battle import Battle
from tuxemon.db import OutputBattle
from tuxemon.event.eventaction import EventAction

logger = logging.getLogger(__name__)


@final
@dataclass
class SetBattleAction(EventAction):
    """
    Append the element in player.battles.

    Script usage:
        .. code-block::

            set_battle <character>,<result>

    Script parameters:
        character: Npc slug name (e.g. "npc_maple").
        result: One among "won", "lost" or "draw"

    """

    name = "set_battle"
    battle_opponent: str
    battle_outcome: str

    def start(self) -> None:
        player = self.session.player

        new_battle = Battle()
        new_battle.opponent = self.battle_opponent
        new_battle.date = dt.date.today().toordinal()

        if self.battle_outcome == "won":
            new_battle.outcome = OutputBattle.won
        elif self.battle_outcome == "draw":
            new_battle.outcome = OutputBattle.draw
        elif self.battle_outcome == "lost":
            new_battle.outcome = OutputBattle.lost
        else:
            logger.error(f"{self.battle_outcome} must be won, lost or draw.")
            raise ValueError()

        player.battles.append(new_battle)
