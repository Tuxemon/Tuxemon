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

from tuxemon.event.eventaction import EventAction


class PlayerMoveAction(EventAction):
    """Makes the player move.

    * Player will move in the direction it is facing
    * Player will move as if moved by primary locomotion; ie "walking with legs"

    If you wish to move the player without walking consider
     * teleporting if the distance is greater than one tile
     * gliding (not implemented)

    Valid Parameters: None
    """

    name = "player_move"
    valid_parameters = []

    def start(self):
        npc = self.context.player
        npc.move_direction(npc.facing)

    def update(self):
        npc = self.context.player
        npc.animation = "walking"
        self.stop()
