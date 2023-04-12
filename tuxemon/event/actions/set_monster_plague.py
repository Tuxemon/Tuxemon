# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import Union, final

from tuxemon.db import PlagueType
from tuxemon.event.eventaction import EventAction


@final
@dataclass
class SetMonsterPlagueAction(EventAction):
    """
    Cure or infect a monster.

    Script usage:
        .. code-block::

            set_monster_plague condition[,slot]

    Script parameters:
        condition: inoculated, sickless or infected
        slot: Slot of the monster in the party. If no slot is specified, all
            monsters are touched by the action.

    """

    name = "set_monster_plague"
    condition: str
    slot: Union[int, None] = None

    def start(self) -> None:
        player = self.session.player
        if not player.monsters:
            return

        monster_slot = self.slot

        if monster_slot is None:
            for monster in player.monsters:
                if self.condition == "inoculated":
                    monster.plague = PlagueType.inoculated
                elif self.condition == "infected":
                    monster.plague = PlagueType.infected
                elif self.condition == "sickless":
                    monster.plague = PlagueType.sickless
                else:
                    raise ValueError(
                        f"{self.condition} must be infect or heal"
                    )
        else:
            mon = self.session.player.monsters[monster_slot]
            if self.condition == "inoculated":
                mon.plague = PlagueType.inoculated
            elif self.condition == "infected":
                mon.plague = PlagueType.infected
            elif self.condition == "sickless":
                mon.plague = PlagueType.sickless
            else:
                raise ValueError(f"{self.condition} must be infect or heal")
