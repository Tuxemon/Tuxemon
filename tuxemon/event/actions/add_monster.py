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

import string
from typing import NamedTuple, Optional, Union, final

from tuxemon import monster
from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.npc import NPC


class AddMonsterActionParameters(NamedTuple):
    monster_slug: str
    monster_level: int
    trainer_slug: Union[str, None]


@final
class AddMonsterAction(EventAction[AddMonsterActionParameters]):
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
    param_class = AddMonsterActionParameters

    def start(self) -> None:

        monster_slug, monster_level, trainer_slug = self.parameters

        trainer: Optional[NPC]
        if trainer_slug is None:
            trainer = self.session.player
        else:
            trainer = get_npc(self.session, trainer_slug)

        assert trainer, "No Trainer found with slug '{}'".format(
            trainer_slug or "player"
        )

        current_monster = monster.Monster()
        current_monster.load_from_db(monster_slug)
        current_monster.set_level(monster_level)
        current_monster.current_hp = current_monster.hp

        string.capwords(trainer.add_monster(current_monster))
