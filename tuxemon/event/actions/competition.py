# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
import uuid
from dataclasses import dataclass
from typing import List, final

from tuxemon.db import StatType
from tuxemon.event.eventaction import EventAction
from tuxemon.monster import Monster


@final
@dataclass
class CompetitionAction(EventAction):
    """
    A selected monster will compete against others based on a specific stat.

    Script usage:
        .. code-block::

            competition <instance_id>,<stat>,<adversaries>

    Script parameters:
        instance_id: Variable where is saved
        stat: Statistic to use (eg speed, armour, etc.)
        adversaries: Slug monsters

    eg "competition name_variable,speed,tumbleworm:apeoro:rockitten"

    """

    name = "competition"
    instance_id: str
    stat: StatType
    adversaries: str

    def start(self) -> None:
        player = self.session.player

        iid = uuid.UUID(player.game_variables[self.instance_id])
        participant = player.find_monster_by_id(iid)
        assert participant

        adversaries: List[str] = []
        if self.adversaries.find(":"):
            adversaries = self.adversaries.split(":")
        else:
            adversaries.append(self.adversaries)

        monsters: List[Monster] = []
        for m in adversaries:
            mon = Monster()
            mon.load_from_db(m)
            mon.set_level(participant.level)
            monsters.append(mon)

        # add us
        monsters.append(participant)

        results = []
        for mon in monsters:
            stat = mon.return_stat(self.stat)
            res = sum(random.randint(1, stat) for x in range(10))
            results.append((res, mon.name.upper(), str(mon.instance_id.hex)))
            results.sort(key=lambda x: x[0], reverse=True)

        for i, name in enumerate(results, 1):
            # save ranking variables
            player.game_variables[f"comp_rank_{i}"] = f"{name[1]} ({name[0]})"
            # replace the variable with iid with the ranking
            if name[2] == player.game_variables[self.instance_id]:
                player.game_variables[self.instance_id] = i
