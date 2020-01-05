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


class EvolveMonstersAction(EventAction):
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
                if evolution['path'] == self.parameters.path:
                    level_over = evolution['at_level'] > 0 and current_monster.level >= evolution['at_level']
                    level_under = evolution['at_level'] < 0 and current_monster.level <= -evolution['at_level']
                    if level_over or level_under:
                        # TODO: implement an evolution animation

                        # Store the properties of the old monster then remove it
                        old_level = current_monster.level
                        old_current_hp = current_monster.current_hp
                        old_name = current_monster.name
                        player.remove_monster(current_monster)

                        # Add the new monster and load the old properties
                        new_monster = monster.Monster()
                        new_monster.load_from_db(evolution['slug'])
                        new_monster.set_level(old_level)
                        new_monster.current_hp = min(old_current_hp, new_monster.hp)
                        new_monster.name = old_name
                        player.add_monster(new_monster)

                        # Removing the old monster caused all monsters in front to move a slot back
                        # Bring our new monster from the end of the list to its previous slot
                        for i in range(len(player.monsters) - 1, slot, -1):
                            player.switch_monsters(i, i - 1)

                        # We executed an evolution for this monster, don't keep looking
                        break
