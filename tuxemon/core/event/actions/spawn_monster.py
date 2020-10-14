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

logger = logging.getLogger(__name__)


# noinspection PyAttributeOutsideInit
class SpawnMonsterAction(EventAction):
    """ Adds a new monster, created by breeding the two
    given mons (identified by instance_id, may be
    optionally stored in a variable) and adds it to the
    given character's party (identified by slug).

    Valid Parameters: trainer, breeding_mother, breeding_father

    **Examples:**

    >>> EventAction.__dict__
    {
        "type": "spawn_monster",
        "parameters": [
            "npc_red",
            "123e4567-e89b-12d3-a456-426614174000",
            "123e4567-e89b-12d3-a456-426614174001"
        ]
    }

    """
    name = "get_step_count"
    valid_parameters = [
        (str, "variable_name")
    ]

    def start(self):
        player = self.session.player
        variable = self.parameters.variable_name
        player.game_variables[variable] = player.game_variables['steps']
