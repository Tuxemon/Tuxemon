# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import final

from tuxemon.db import PlagueType
from tuxemon.event.eventaction import EventAction


@final
@dataclass
class QuarantineAction(EventAction):
    """
    Quarantine infected monsters.

    Script usage:
        .. code-block::

            quarantine <value>

    Script parameters:
        value: in or out

    """

    name = "quarantine"
    value: str

    def start(self) -> None:
        player = self.session.player
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
            for ele in box:
                ele.plague = PlagueType.inoculated
                player.add_monster(ele, len(player.monsters))
                player.monster_boxes["quarantine"].remove(ele)
        else:
            raise ValueError(f"{self.value} must be in or out")
