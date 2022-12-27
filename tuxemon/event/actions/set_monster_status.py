# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, Union, final

from tuxemon.event.eventaction import EventAction
from tuxemon.monster import Monster
from tuxemon.technique.technique import Technique

logger = logging.getLogger(__name__)


@final
@dataclass
class SetMonsterStatusAction(EventAction):
    """
    Change the status of a monster in the current player's party.

    Script usage:
        .. code-block::

            set_monster_status [slot][,status]

    Script parameters:
        slot: Slot of the monster in the party. If no slot is specified, all
            monsters are modified.
        status: Status to set. If no status is specified, the status is
            cleared.

    """

    name = "set_monster_status"
    slot: Union[int, None] = None
    status: Union[str, None] = None

    @staticmethod
    def set_status(monster: Monster, value: Optional[str]) -> None:
        if not value:
            monster.status = list()
        else:
            # TODO: own class for status effect
            # TODO: handle invalid statues
            status = Technique(value)
            monster.apply_status(status)

    def start(self) -> None:
        if not self.session.player.monsters:
            return

        if self.slot is None:
            for monster in self.session.player.monsters:
                self.set_status(monster, self.status)
        else:
            try:
                monster = self.session.player.monsters[self.slot]
            except IndexError:
                logger.error("invalid monster slot")
            else:
                self.set_status(monster, self.status)
