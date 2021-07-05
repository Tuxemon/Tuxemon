#
# Tuxemon
# Copyright (c) 2020      William Edwards <shadowapex@gmail.com>,
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
# Contributor(s):
#
# Adam Chevalier <chevalierAdam2@gmail.com>

from __future__ import annotations
from tuxemon.event.eventaction import EventAction
import logging
import uuid
from typing import NamedTuple, final

logger = logging.getLogger(__name__)


class StoreMonsterActionParameters(NamedTuple):
    monster_id: str
    box: str


# noinspection PyAttributeOutsideInit
@final
class StoreMonsterAction(EventAction[StoreMonsterActionParameters]):
    """Save the player's monster with the given instance_id to
    the named storage box, removing it from the player party.

    Valid Parameters: string monster_id, string box
    """

    name = "store_monster"
    param_class = StoreMonsterActionParameters

    def start(self) -> None:
        player = self.session.player
        instance_id = uuid.UUID(player.game_variables[self.parameters.monster_id])
        box = self.parameters.box
        monster = player.find_monster_by_id(instance_id)
        if monster is None:
            raise ValueError(f"No monster found with instance_id {instance_id}")

        if box not in player.monster_boxes.keys():
            player.monster_boxes[box] = list()

        player.monster_boxes[box].append(monster)
        player.remove_monster(monster)
