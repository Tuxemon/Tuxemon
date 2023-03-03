# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import final

from tuxemon import battle
from tuxemon.db import OutputBattle
from tuxemon.event.eventaction import EventAction


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

        new_battle = battle.Battle()
        new_battle.opponent = self.battle_opponent
        new_battle.outcome = self.battle_outcome
        new_battle.date = dt.date.today().toordinal()

        outcomes = [otc.value for otc in OutputBattle]
        if self.battle_outcome in outcomes:
            player.battles.append(new_battle)
        else:
            return
