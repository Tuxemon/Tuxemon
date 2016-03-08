#!/usr/bin/python
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
#
# core.components.ai Artificial intelligence module.
#
#

import logging

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)
logger.debug("%s successfully imported" % __name__)


# Class definition for an AI model.
class AI(object):
    """A class for an AI model object. This object can be used to make combat decisions during
    battle.

    """
    def __init__(self):
        self.name = "Idiot"			# This is the player's name to be used in dialog


    def make_decision(self, npc, opponent):
        """Examples:

        >>> npc
        {'action': None,
         'monster': <core.monster.Monster instance at 0x7f9d80733680>,
         'monster_last_hp': 50,
         'monster_sprite': {'position': (960, 0), 'surface': <Surface(320x320x32 SW)>},
         'player': <core.player.Npc instance at 0x7f9d807338c0>}
        >>> opponent
        {'action': None,
         'monster': <core.monster.Monster instance at 0x7f9d80733a70>,
         'monster_last_hp': 30,
         'monster_level_text': {'font': <pygame.font.Font object at 0x7f9d8094b290>,
                                'position': (1210, 385),
                                'surface': <Surface(35x36x32 SW)>},
         'monster_sprite': {'position': (0, 280), 'surface': <Surface(320x320x32 SW)>},
         'player': <core.player.Player instance at 0x7f9d80977c20>}


        """
        logger.info("Making descision")

        #pprint.pprint(npc['monster'].__dict__)
        #pprint.pprint(opponent)

        return {'technique': 0}



class PseudoAI(object):
    """A class to provide networking input to an opponents Npc object. This object can be used to push combat decisions during
    battle from one client to another.

    """
    def __init__(self, npc):
        self.name = npc.name            # This is the player's name to be used in dialog

    def make_decision(self, npc, opponent):
        """Examples:

        >>> npc
        {'action': None,
         'monster': <core.monster.Monster instance at 0x7f9d80733680>,
         'monster_last_hp': 50,
         'monster_sprite': {'position': (960, 0), 'surface': <Surface(320x320x32 SW)>},
         'player': <core.player.Npc instance at 0x7f9d807338c0>}
        >>> opponent
        {'action': None,
         'monster': <core.monster.Monster instance at 0x7f9d80733a70>,
         'monster_last_hp': 30,
         'monster_level_text': {'font': <pygame.font.Font object at 0x7f9d8094b290>,
                                'position': (1210, 385),
                                'surface': <Surface(35x36x32 SW)>},
         'monster_sprite': {'position': (0, 280), 'surface': <Surface(320x320x32 SW)>},
         'player': <core.player.Player instance at 0x7f9d80977c20>}


        """


        logger.info("Opponent has made a move.")

        #pprint.pprint(npc['monster'].__dict__)
        #pprint.pprint(opponent)

        return {'technique': 0}

