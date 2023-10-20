# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import Union, final

from tuxemon.event.eventaction import EventAction
from tuxemon.monster import Monster
from tuxemon.technique.technique import Technique


@final
@dataclass
class SetMonsterLevelAction(EventAction):
    """
    Change the level of a monster in the current player's party.

    Script usage:
        .. code-block::

            set_monster_level [level][,slot]

    Script parameters:
        level: Number of levels to add. Negative numbers are allowed.
        slot: Slot of the monster in the party. If no slot is specified, all
            monsters are leveled.

    """

    name = "set_monster_level"
    level: int
    slot: Union[int, None] = None

    def start(self) -> None:
        if not self.session.player.monsters:
            return

        def update_move(mon: Monster, level: int) -> None:
            for move in mon.moveset:
                if (
                    move.technique not in (m.slug for m in mon.moves)
                    and move.level_learned <= level
                ):
                    technique = Technique()
                    technique.load(move.technique)
                    mon.learn(technique)

        monster_slot = self.slot
        monster_level = self.level

        if monster_slot is not None:
            if len(self.session.player.monsters) < int(monster_slot):
                return

            monster = self.session.player.monsters[int(monster_slot)]
            new_level = monster.level + int(monster_level)
            monster.set_level(new_level)
            update_move(monster, new_level)
        else:
            for monster in self.session.player.monsters:
                new_level = monster.level + int(monster_level)
                monster.set_level(new_level)
                update_move(monster, new_level)
