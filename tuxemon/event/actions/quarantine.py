# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from typing import Union, final

from tuxemon.db import PlagueType
from tuxemon.event.eventaction import EventAction

logger = logging.getLogger(__name__)


@final
@dataclass
class QuarantineAction(EventAction):
    """
    Quarantine infected monsters.
    Amount works only for "out", it takes out the amount in a random way.

    Script usage:
        .. code-block::

            quarantine <value>[,amount]

    Script parameters:
        value: in or out
        amount: number of monsters

    e.g. "quarantine out,5" (5 monsters out by random)

    """

    name = "quarantine"
    value: str
    amount: Union[int, None] = None

    def start(self) -> None:
        player = self.session.player
        if self.name not in player.monster_boxes.keys():
            player.monster_boxes[self.name] = []
        if self.value == "in":
            infect = PlagueType.infected
            plague = [mon for mon in player.monsters if mon.plague == infect]
            for _monster in plague:
                _monster.plague = PlagueType.inoculated
                player.monster_boxes[self.name].append(_monster)
                player.remove_monster(_monster)
                logger.info(f"{_monster} has been quarantined")
        elif self.value == "out":
            box = [mon for mon in player.monster_boxes[self.name]]
            if not box:
                logger.info(f"Box {self.name} is empty")
                return
            if self.amount is None or self.amount >= len(box):
                for _monster in box:
                    _monster.plague = PlagueType.inoculated
                    player.add_monster(_monster, len(player.monsters))
                    player.monster_boxes[self.name].remove(_monster)
                    logger.info(f"{_monster} has been inoculated")
            else:
                sample = random.sample(box, self.amount)
                for _monster in sample:
                    _monster.plague = PlagueType.inoculated
                    player.add_monster(_monster, len(player.monsters))
                    player.monster_boxes[self.name].remove(_monster)
                    logger.info(f"{_monster} has been inoculated")
        else:
            raise ValueError(f"{self.value} must be in or out")
