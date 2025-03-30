# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
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
    Quarantine or release monsters infected with a specific plague.

    Usage:
        quarantine <plague_slug>,<value>[,amount]

    Parameters:
        plague_slug: The slug of the plague to target.
        value: "in" to quarantine infected monsters, "out" to release them.
        amount: (Optional, only for "out") The number of monsters to release
            randomly.

    Example: "quarantine out,5" (Release 5 infected monsters randomly)
    """

    name = "quarantine"
    plague_slug: str
    value: str
    amount: Union[int, None] = None

    def start(self) -> None:
        player = self.session.player
        if not player.monster_boxes.has_box(self.name, "monster"):
            player.monster_boxes.create_box(self.name, "monster")
        if self.value == "in":
            infect = PlagueType.infected
            plague = [
                mon
                for mon in player.monsters
                if self.plague_slug in mon.plague
                and mon.plague[self.plague_slug] == infect
            ]
            for _monster in plague:
                _monster.plague[self.plague_slug] = PlagueType.inoculated
                player.monster_boxes.add_monster(self.name, _monster)
                player.remove_monster(_monster)
                logger.info(f"{_monster} has been quarantined")
        elif self.value == "out":
            if not player.monster_boxes.has_box(self.name, "monster"):
                logger.info(f"Box {self.name} does not exist")
                return
            box = [
                mon
                for mon in player.monster_boxes.get_monsters(self.name)
                if self.plague_slug in mon.plague
            ]
            if not box:
                logger.info(f"Box {self.name} is empty")
                return
            if self.amount is None or self.amount >= len(box):
                for _monster in box:
                    _monster.plague[self.plague_slug] = PlagueType.inoculated
                    player.add_monster(_monster, len(player.monsters))
                    player.monster_boxes.remove_monster_from(
                        self.name, _monster
                    )
                    logger.info(f"{_monster} has been inoculated")
            elif self.amount > 0 and self.amount <= len(box):
                sample = random.sample(box, self.amount)
                for _monster in sample:
                    _monster.plague[self.plague_slug] = PlagueType.inoculated
                    player.add_monster(_monster, len(player.monsters))
                    player.monster_boxes.remove_monster_from(
                        self.name, _monster
                    )
                    logger.info(f"{_monster} has been inoculated")
            else:
                logger.info(f"Invalid sample size")
        else:
            raise ValueError(f"{self.value} must be in or out")
