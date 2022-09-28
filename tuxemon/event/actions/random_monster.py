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

import random as rd
from typing import NamedTuple, Optional, Union, final

from tuxemon import monster
from tuxemon.db import db
from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.npc import NPC


class RandomMonsterActionParameters(NamedTuple):
    monster_level: int
    trainer_slug: Union[str, None]


@final
class RandomMonsterAction(EventAction[RandomMonsterActionParameters]):
    """
    Add a monster to the specified trainer's party if there is room.

    Script usage:
        .. code-block::

            random_monster <monster_level>[,trainer_slug]

    Script parameters:
        monster_level: Level of the added monster.
        trainer_slug: Slug of the trainer that will receive the monster. It
            defaults to the current player.

    """

    name = "random_monster"
    param_class = RandomMonsterActionParameters

    def start(self) -> None:

        monster_level, trainer_slug = self.parameters

        trainer: Optional[NPC]
        if trainer_slug is None:
            trainer = self.session.player
        else:
            trainer = get_npc(self.session, trainer_slug)

        assert trainer, "No Trainer found with slug '{}'".format(
            trainer_slug or "player"
        )

        # list is required as choice expects a sequence
        monster_slug = rd.choice(list(db.database["monster"]))

        current_monster = monster.Monster()
        current_monster.load_from_db(monster_slug)
        current_monster.set_level(monster_level)
        current_monster.current_hp = current_monster.hp

        trainer.add_monster(current_monster)
