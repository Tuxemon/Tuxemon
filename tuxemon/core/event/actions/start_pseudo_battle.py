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


class StartPseudoBattleAction(EventAction):
    """ Start a networked duel and switch to the combat module.
    """
    name = "start_pseudo_battle"
    valid_parameters = []

    def start(self):
        player = self.game.player1

        # Don't start a battle if we don't even have monsters in our party yet.
        if not check_battle_legal(player):
            return False

        if not check_battle_legal(npc):
            return False

        # Stop movement and keypress on the server.
        if self.game.isclient or self.game.ishost:
            self.game.client.update_player(player.facing, event_type="CLIENT_START_BATTLE")

        # Lookup the environment
        env_slug = "grass"
        if 'environment' in player.game_variables:
            env_slug = player.game_variables['environment']
        env = db.lookup(env_slug, table="environment")

        # Add our players and setup combat
        self.game.push_state("CombatState", players=(player, npc), combat_type="trainer",
                             graphics=env['battle_graphics'])

        # flash the screen
        self.game.push_state("FlashTransition")

        # Start some music!
        logger.info("Playing battle music!")
        filename = env['battle_music']

        # mixer.music.load(prepare.fetch("music", filename))
        # mixer.music.play(-1)
