# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

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
    Append a new element in player.battles.

    Script usage:
        .. code-block::

            set_battle <fighter>,<result>,<opponent>

    Script parameters:
        fighter: Npc slug name (e.g. "npc_maple").
        result: One among "won", "lost" and "draw".
        opponent: Npc slug name (e.g. "npc_maple").

    eg. "set_battle player,won,npc_maple"
        -> player won against npc_maple

    """

    name = "set_battle"
    fighter: str
    outcome: str
    opponent: str

    def start(self) -> None:
        player = self.session.player

        _output = list(OutputBattle)
        if self.outcome not in _output:
            raise ValueError(f"{self.outcome} isn't among {_output}")

        battle = Battle()
        battle.fighter = self.fighter
        battle.outcome = OutputBattle(self.outcome)
        battle.opponent = self.opponent
        battle.steps = int(player.steps)
        logger.info(f"{self.fighter} {self.outcome} against {self.opponent}")
        player.battles.append(battle)
