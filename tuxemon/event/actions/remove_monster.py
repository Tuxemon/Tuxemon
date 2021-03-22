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
import uuid

from tuxemon.event.eventaction import EventAction
from tuxemon.event import get_npc


class RemoveMonsterAction(EventAction):
    """Removes a monster from the given trainer's party if the monster is there.
    Monster is determined by instance_id, which must be passed in a game variable.
    If no trainer slug is passed it defaults to the current player.

    Valid Parameters: instance_id
    """

    name = "remove_monster"
    valid_parameters = [(str, "instance_id"), ((str, None), "trainer_slug")]

    def start(self):
        iid = self.session.player.game_variables[self.parameters.instance_id]
        instance_id = uuid.UUID(iid)
        trainer_slug = self.parameters.trainer

        if trainer_slug is None:
            trainer = self.session.player
        else:
            trainer = get_npc(trainer_slug)

        monster = trainer.find_monster_by_id(instance_id)
        if monster is not None:
            self.session.player.remove_monster(monster)
