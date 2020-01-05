# -*- coding: utf-8 -*-
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
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from tuxemon.core.components import monster
from tuxemon.core.components.event.eventaction import EventAction


class EvolveMonsterAction(EventAction):
    """Evolves all monsters in the player's party for the specified evolutionary path.

    Valid Parameters: path
    """
    name = "evolve_monsters"
    valid_parameters = [
        (str, "path")
    ]

    def start(self):
        player = self.game.player1
        for slot in range(len(player.monsters)):
            current_monster = player.monsters[slot]
            for evolution in current_monster.evolutions:
                if evolution['name'] == self.parameters.path and current_monster.level >= evolution['at_level']:
                    # TODO: implement an evolution animation

                    # Add the new monster
                    new_monster = monster.Monster()
                    new_monster.load_from_db(evolution['slug'])
                    new_monster.set_level(current_monster.level)
                    new_monster.current_hp = min(current_monster.current_hp, new_monster.hp)
                    new_monster.name = current_monster.name
                    player.add_monster(new_monster)

                    # Put the new monster in the slot of the old monster
                    player.switch_monsters(slot, len(player.monsters) - 1)

                    # Remove the old monster
                    player.remove_monster(current_monster)

                    # We executed an evolution for this monster, don't keep looking
                    break
