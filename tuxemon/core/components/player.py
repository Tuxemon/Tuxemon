# -*- coding: utf-8 -*-
#
# Tuxemon
# Copyright (C) 2014, William Edwards <shadowapex@gmail.com>,
#                     Benjamin Bean <superman2k5@gmail.com>
#
# This file is part of Tuxemon.
#
# Tuxemon is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Tuxemon is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Tuxemon.  If not, see <http://www.gnu.org/licenses/>.
#
# Contributor(s):
#
# William Edwards <shadowapex@gmail.com>
# Derek Clark <derekjohn.clark@gmail.com>
# Leif Theden <leif.theden@gmail.com>
#
# core.components.player
#
from __future__ import absolute_import, division

import logging

from core.components.npc import Npc

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)


# Class definition for the player.
class Player(Npc):
    """ Object for Players.  WIP
    """
    # The maximum number of tuxemon this player can hold
    party_limit = 6
    isplayer = True

    def __init__(self, npc_slug):
        super(Player, self).__init__(npc_slug)

        # Game variables for use with events
        self.game_variables = {}

        # This is a list of tuxemon the player has
        self.monsters = []
        self.storage = {"monsters": [], "items": {}}

    def add_monster(self, monster):
        """Adds a monster to the player's list of monsters. If the player's party is full, it
        will send the monster to PCState archive.

        :param monster: The core.components.monster.Monster object to add to the player's party.

        :type monster: core.components.monster.Monster

        :rtype: None
        :returns: None

        """
        if len(self.monsters) >= self.party_limit:
            self.storage["monsters"].append(monster)
        else:
            self.monsters.append(monster)

    def find_monster(self, monster_slug):
        """Finds a monster in the player's list of monsters.

        :param monster_slug: The slug name of the monster
        :type monster_slug: str

        :rtype: core.components.monster.Monster
        :returns: Monster found
        """
        for monster in self.monsters:
            if monster.slug == monster_slug:
                return monster
        return None

    def remove_monster(self, monster):
        """ Removes a monster from this player's party.

        :param monster: Monster to remove from the player's party.

        :type monster: core.components.monster.Monster

        :rtype: None
        :returns: None
        """
        if monster in self.monsters:
            self.monsters.remove(monster)

    def switch_monsters(self, index_1, index_2):
        """ Swap two monsters in this player's party

        :param index_1/index_2: The indexes of the monsters to switch in the player's party.

        :type index_1: int
        :type index_2: int

        :rtype: None
        :returns: None
        """
        self.monsters[index_1], self.monsters[index_2] = self.monsters[index_2], self.monsters[index_1]
