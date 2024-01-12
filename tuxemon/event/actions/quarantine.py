# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Union, final

from tuxemon.db import PlagueType
from tuxemon.event.eventaction import EventAction


@final
@dataclass
class QuarantineAction(EventAction):
    """
    Quarantine infected monsters.
    Amount works only for "out", it takes out
    the amount in a random way.

    E.g. box contains 30 monster
    quarantine out,5
    5 monsters by random

    Script usage:
        .. code-block::

            quarantine <value>[,amount]

    Script parameters:
        value: in or out
        amount: number of monsters

    """

    name = "quarantine"
    value: str
    amount: Union[int, None] = None

    def start(self) -> None:
        player = self.session.player
        if "quarantine" not in player.monster_boxes.keys():
            player.monster_boxes["quarantine"] = []
        if self.value == "in":
            infected = [
                ele
                for ele in player.monsters
                if ele.plague == PlagueType.infected
            ]
            for ele in infected:
                player.monster_boxes["quarantine"].append(ele)
                player.remove_monster(ele)
        elif self.value == "out":
            box = [mon for mon in player.monster_boxes["quarantine"]]
            # empty the box
            if self.amount is None or self.amount >= len(box):
                for ele in box:
                    ele.plague = PlagueType.inoculated
                    player.add_monster(ele, len(player.monsters))
                    player.monster_boxes["quarantine"].remove(ele)
            else:
                sample = random.sample(box, self.amount)
                for sam in sample:
                    sam.plague = PlagueType.inoculated
                    player.add_monster(sam, len(player.monsters))
                    player.monster_boxes["quarantine"].remove(sam)
        else:
            raise ValueError(f"{self.value} must be in or out")
