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

from tuxemon.core.event.eventaction import EventAction
import logging
import uuid

logger = logging.getLogger(__name__)


class WithdrawMonsterAction(EventAction):
    """
    Pulls a monster from the given trainer's storage (identified by slug and instance_id respectively)
    and puts it in their party. Note: If the trainer's party is already full then the monster will be
    deposited into the default storage box automatically.

    Valid Parameters: trainer, monster_id

    **Examples:**

    >>> EventAction.__dict__
    {
        "type": "withdraw_monster",
        "parameters": [
            "npc_red",
            "123e4567-e89b-12d3-a456-426614174000"
        ]
    }


    """
    name = "withdraw_monster"
    valid_parameters = [
        (str, "trainer"),
        (str, "monster_id")
    ]

    def start(self):
        trainer, monster_id = self.parameters
        world = self.session.client.get_state_by_name("WorldState")
        if not world:
            return False

        trainer = trainer.replace("player", "npc_red")
        npc = world.get_entity(trainer)
        instance_id = uuid.UUID(npc.game_variables[monster_id])
        mon = npc.find_monster_in_storage(instance_id)

        npc.remove_monster_from_storage(mon)
        npc.add_monster(mon)
