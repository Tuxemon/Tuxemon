# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, Union, final

from tuxemon.event.eventaction import EventAction
from tuxemon.monster import Monster

logger = logging.getLogger(__name__)


@final
@dataclass
class SetMonsterHealthAction(EventAction):
    """
    Change the hp of a monster in the current player's party.

    Script usage:
        .. code-block::

            set_monster_health [slot][,health]

    Script parameters:
        slot: Slot of the monster in the party. If no slot is specified, all
            monsters are healed.
        health: A float value between 0 and 1, which is the percent of max
            hp to be restored to. If no health is specified, the hp is maxed
            out.

    """

    name = "set_monster_health"
    slot: Union[int, None] = None
    health: Union[float, None] = None

    @staticmethod
    def set_health(monster: Monster, value: Optional[float]) -> None:
        if value is None:
            monster.current_hp = monster.hp
        else:
            if not 0 <= value <= 1:
                raise ValueError("monster health must between 0 and 1")

            monster.current_hp = int(monster.hp * value)

    def start(self) -> None:
        if not self.session.player.monsters:
            return

        monster_slot = self.slot
        monster_health = self.health

        if monster_slot is None:
            for monster in self.session.player.monsters:
                self.set_health(monster, monster_health)
        else:
            try:
                monster = self.session.player.monsters[monster_slot]
            except IndexError:
                logger.error("invalid monster slot")
            else:
                self.set_health(monster, monster_health)
