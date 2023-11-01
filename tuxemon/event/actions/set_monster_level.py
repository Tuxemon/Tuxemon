# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, final

from tuxemon.event.eventaction import EventAction


@final
@dataclass
class SetMonsterLevelAction(EventAction):
    """
    Change the level of a monster in the current player's party.

    Script usage:
        .. code-block::

            set_monster_level [levels_added][,slot]

    Script parameters:
        levels_added: Number of levels to add. Negative numbers are allowed.
        slot: Slot of the monster in the party. If no slot is specified, all
            monsters are leveled.

    """

    name = "set_monster_level"
    levels_added: int
    slot: Optional[int] = None

    def start(self) -> None:
        player = self.session.player
        if not player.monsters:
            return

        if self.slot is not None:
            # check if it's inserted the wrong value
            if self.slot > len(player.monsters):
                return

            monster = player.monsters[self.slot]
            new_level = monster.level + self.levels_added
            monster.set_level(new_level)
            monster.update_moves(self.levels_added)
        else:
            for monster in player.monsters:
                new_level = monster.level + self.levels_added
                monster.set_level(new_level)
                monster.update_moves(self.levels_added)
