# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import final

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction

logger = logging.getLogger(__name__)


@final
@dataclass
class WithdrawMonsterAction(EventAction):
    """
    Pull a monster from the given trainer's storage and puts it in their party.

    Note:
        If the trainer's party is already full then the monster will be
        deposited into the default storage box automatically.

    Script usage:
        .. code-block::

            withdraw_monster <variable>,<character>

    Script parameters:
        variable: Name of the variable where to store the monster id.
        character: Either "player" or npc slug name (e.g. "npc_maple").
            the one who is going to receive the monster

    """

    name = "withdraw_monster"
    variable: str
    character: str

    def start(self) -> None:
        player = self.session.player
        if self.variable not in player.game_variables:
            logger.error(f"Game variable {self.variable} not found")
            return

        monster_id = uuid.UUID(player.game_variables[self.variable])
        monster = player.find_monster_in_storage(monster_id)
        if monster is None:
            logger.error("Monster not found")
            return
        player.remove_monster_from_storage(monster)

        character = get_npc(self.session, self.character)
        if character is None:
            logger.error(f"{self.character} not found")
            return

        character.add_monster(monster, len(character.monsters))
        logger.info(f"{character.name} withdrawn {monster.name}!")
