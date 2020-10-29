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

import logging

from tuxemon.core.event.eventaction import EventAction
from tuxemon.core.technique import Technique

logger = logging.getLogger(__name__)


class SetMonsterStatusAction(EventAction):
    """ Changes the status of a monster in the current player's party. The action parameters
    may contain a monster slot and the new status to be appended. If no slot is specified,
    all monsters are modified. If no status is specified, the status is cleared.

    Valid Parameters: slot, status
    """
    name = "set_monster_status"
    valid_parameters = [
        (int, "slot"),
        (str, "status")
    ]

    @staticmethod
    def set_status(monster, value):
        if value is None:
            monster.status = list()
        else:
            # TODO: own class for status effect
            # TODO: handle invalid statues
            status = Technique(value)
            monster.apply_status(status)

    def start(self):
        if not self.session.player.monsters:
            return

        monster_slot = self.parameters[0]
        monster_status = self.parameters[1]

        if monster_slot is None:
            for monster in self.session.player.monsters:
                self.set_status(monster, monster_status)
        else:
            try:
                monster = self.session.player.monsters[monster_slot]
            except IndexError:
                logger.error("invalid monster slot")
            else:
                self.set_status(monster, monster_status)
