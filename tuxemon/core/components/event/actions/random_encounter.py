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
import random

from tuxemon.core import tools
from tuxemon.core.components import ai, db, monster
from tuxemon.core.components.event.actions import check_battle_legal
from tuxemon.core.components.event.eventaction import EventAction
from tuxemon.core.components.npc import NPC
from tuxemon.core.platform import mixer

logger = logging.getLogger(__name__)


class RandomEncounterAction(EventAction):
    """ Randomly starts a battle with a monster defined in the "encounter" table in the
    "monster.db" database. The chance that this will start a battle depends on the
    "encounter_rate" specified in the database. The "encounter_rate" number is the chance
    walking in to this tile will trigger a battle out of 100.

    Valid Parameters: encounter_slug
    """
    name = "random_encounter"
    valid_parameters = [
        (str, "encounter_slug"),
    ]

    def start(self):
        player1 = self.game.player1

        # Don't start a battle if we don't even have monsters in our party yet.
        if not check_battle_legal(player1):
            return False

        # Get the parameters to determine what encounter group we'll look up in the database.
        encounter_slug = self.parameters.encounter_slug

        # Look up the encounter details
        monsters = db.JSONDatabase()
        monsters.load("encounter")
        monsters.load("monster")

        # Keep an encounter variable that will let us know if we're going to start a battle.
        encounter = None

        # Get all the monsters associated with this encounter.
        encounters = monsters.database['encounter'][encounter_slug]['monsters']

        for item in encounters:
            # Perform a roll to see if this monster is going to start a battle.
            roll = random.randrange(1, 1000)
            if roll <= int(item['encounter_rate']):
                # Set our encounter details
                encounter = item

        # If a random encounter was successfully rolled, look up the monster and start the
        # battle.
        if encounter:
            logger.info("Starting random encounter!")

            player1.stop_moving()
            player1.cancel_path()

            # Stop movement and keypress on the server.
            if self.game.isclient or self.game.ishost:
                self.game.client.update_player(self.game.player1.facing, event_type="CLIENT_START_BATTLE")

            # Create a monster object
            current_monster = monster.Monster()
            current_monster.load_from_db(encounter['monster'])

            # Set the monster's level based on the specified level range
            if len(encounter['level_range']) > 1:
                level = random.randrange(encounter['level_range'][0], encounter['level_range'][1])
            else:
                level = encounter['level_range'][0]

            # Set the monster's level
            current_monster.level = 1
            current_monster.set_level(level)
            current_monster.current_hp = current_monster.hp

            # Create an NPC object which will be this monster's "trainer"
            npc = NPC("maple_girl")
            npc.monsters.append(current_monster)
            npc.party_limit = 0

            # Set the NPC object's AI model.
            npc.ai = ai.AI()

            # Add our players and setup combat
            # "queueing" it will mean it starts after the top of the stack is popped (or replaced)
            self.game.queue_state("CombatState", players=(player1, npc), combat_type="monster")

            # flash the screen
            self.game.push_state("FlashTransition")

            # Start some music!
            filename = "JRPGCollection/ogg/JRPG_battle_loop.ogg"
            mixer.music.load(tools.transform_resource_filename('music', filename))
            mixer.music.play(-1)
            if self.game.current_music["song"]:
                self.game.current_music["previoussong"] = self.game.current_music["song"]
            self.game.current_music["status"] = "playing"
            self.game.current_music["song"] = filename

    def update(self):
        if self.game.get_state_name("CombatState") is None:
            self.stop()
