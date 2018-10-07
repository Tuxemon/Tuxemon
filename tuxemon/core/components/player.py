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

from tuxemon.core.components.npc import NPC

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)


# Class definition for the player.
class Player(NPC):
    """ Object for Players.  WIP
    """

    def __init__(self, npc_slug):
        super(Player, self).__init__(npc_slug)
        self.isplayer = True

        # Game variables for use with events
        self.game_variables = {}
