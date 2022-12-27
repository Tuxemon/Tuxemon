# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction


@final
@dataclass
class SetBattleAction(EventAction):
    """
    Set the key in the player.battle_history dictionary.

    Script usage:
        .. code-block::

            set_battle <character>:<result>

    Script parameters:
        character: Npc slug name (e.g. "npc_maple").
        result: One among "won", "lost" or "draw"

    """

    name = "set_battle"
    battle_list: str

    def start(self) -> None:
        player = self.session.player

        # Split the variable into a key: value pair
        battle_list = self.battle_list.split(":")
        battle_key = str(battle_list[0])
        battle_value = str(battle_list[1]), dt.date.today().toordinal()

        # set the value in battle history
        player.battle_history[battle_key] = battle_value
