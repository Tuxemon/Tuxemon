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

import logging

from core.components.event.actions import check_battle_legal
from core.components.event.eventaction import EventAction

logger = logging.getLogger(__name__)


class StartPseudoBattleAction(EventAction):
    """ Start a networked duel and switch to the combat module.
    """
    name = "start_pseudo_battle"
    valid_parameters = []

    def start(self):
        # Don't start a battle if we don't even have monsters in our party yet.
        if not check_battle_legal(self.game.player1):
            return False

        if not check_battle_legal(npc):
            return False

        # Stop movement and keypress on the server.
        if self.game.isclient or self.game.ishost:
            self.game.client.update_player(self.game.player1.facing, event_type="CLIENT_START_BATTLE")

        # Add our players and setup combat
        self.game.push_state("CombatState", players=(self.game.player1, npc), combat_type="trainer")

        # flash the screen
        self.game.push_state("FlashTransition")

        # Start some music!
        logger.info("Playing battle music!")
        filename = "147066_pokemon.ogg"

        # mixer.music.load(prepare.BASEDIR + prepare.DATADIR + "/music/" + filename)
        # mixer.music.play(-1)
