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

import logging

from tuxemon.core.combat import check_battle_legal
from tuxemon.core.db import db
from tuxemon.core.event.eventaction import EventAction

logger = logging.getLogger(__name__)


class StartBattleAction(EventAction):
    """ Start a battle and switch to the combat module. The parameters must
    contain an NPC slug in the NPC database.

    Valid Parameters: npc_slug

    **Examples:**

    >>> action.__dict__
    {
        "type": "start_battle",
        "parameters": [
            "npc_hiker1"
        ]
    }

    """
    name = "start_battle"
    valid_parameters = [
        (str, "npc_slug")
    ]

    def start(self):
        player = self.game.player1

        # Don't start a battle if we don't even have monsters in our party yet.
        if not check_battle_legal(player):
            logger.debug("battle is not legal: won't start because we don't have enough monsters in our party")
            return False # don't start battle

        # Fetch the antagonist NPC from the world state
        world = self.game.get_state_name("WorldState")
        if not world:
            logger.debug("battle could not be started because WorldState was not obtained")
            return False # don't start battle
        npc = world.get_entity(self.parameters.npc_slug)
        if npc.battled_already:
            logger.debug("battle did not start because this NPC battled the protagonist already") 
            return False
        npc.load_party()

        # Stop movement and keypress on the server.
        if self.game.isclient or self.game.ishost:
            self.game.client.update_player(player.facing, event_type="CLIENT_START_BATTLE")

        # Lookup the environment
        env_slug = "grass"
        if 'environment' in player.game_variables:
            env_slug = player.game_variables['environment']
        env = db.lookup(env_slug, table="environment")

        # Add our players and setup combat
        logger.debug("Starting battle!")
        self.game.push_state("CombatState", players=(player, npc), combat_type="trainer",
                             graphics=env['battle_graphics'])

        # Start some music!
        filename = env['battle_music']
        self.game.event_engine.execute_action("play_music", [filename])

    def update(self):
        # Check if the CombatState no longer exists (hence combat is over)
        if self.game.get_state_name("CombatState") is None:
            npc.battled_already = True 
            self.stop()
