#
# Tuxemon
# Copyright (c) 2014-2017 William Edwards <shadowapex@gmail.com>,
#                         Benjamin Bean <superman2k5@gmail.com>
#
# This file is part of Tuxemon
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Union, final

from tuxemon import monster
from tuxemon.db import SeenStatus
from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.npc import NPC


@final
@dataclass
class AddMonsterAction(EventAction):
    """
    Add a monster to the specified trainer's party if there is room.

    Script usage:
        .. code-block::

            add_monster <monster_slug>,<monster_level>[,trainer_slug]

    Script parameters:
        monster_slug: Monster slug to look up in the monster database.
        monster_level: Level of the added monster.
        trainer_slug: Slug of the trainer that will receive the monster. It
            defaults to the current player.

    """

    name = "add_monster"
    monster_slug: str
    monster_level: int
    trainer_slug: Union[str, None] = None

    def start(self) -> None:

        trainer: Optional[NPC]
        if self.trainer_slug is None:
            trainer = self.session.player
        else:
            trainer = get_npc(self.session, self.trainer_slug)

        assert trainer, "No Trainer found with slug '{}'".format(
            self.trainer_slug or "player"
        )

        current_monster = monster.Monster()
        current_monster.load_from_db(self.monster_slug)
        current_monster.set_level(self.monster_level)
        current_monster.current_hp = current_monster.hp

        trainer.add_monster(current_monster)
        trainer.tuxepedia[self.monster_slug] = SeenStatus.caught
