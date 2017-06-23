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

from core import prepare
from core.components import ai, db, monster, player, technique
from core.components.event.actions import check_battle_legal
from core.components.event.eventaction import EventAction
from core.platform import mixer

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
        # Don't start a battle if we don't even have monsters in our party yet.
        if not check_battle_legal(self.game.player1):
            return False

        # Stop movement and keypress on the server.
        if self.game.isclient or self.game.ishost:
            self.game.client.update_player(self.game.player1.facing, event_type="CLIENT_START_BATTLE")

        # Start combat
        npc_slug = self.parameters.npc_slug

        # TODO: This should *really* be handled in the Npc initializer
        # Create an NPC object that will be used as our opponent
        npc = player.Npc(slug=npc_slug)

        # Look up the NPC's details from our NPC database
        npcs = db.JSONDatabase()
        npcs.load("npc")
        npc_details = npcs.database['npc'][npc_slug]

        # Set the NPC object's AI model.
        npc.ai = ai.AI()

        # Look up the NPC's monster party
        npc_party = npc_details['monsters']

        # Look up the monster's details
        monsters = db.JSONDatabase()
        monsters.load("monster")

        # Look up each monster in the NPC's party
        for npc_monster_details in npc_party:
            results = monsters.database['monster'][npc_monster_details['monster']]

            # Create a monster object for each monster the NPC has in their party.
            # TODO: unify save/load of monsters
            current_monster = monster.Monster()
            current_monster.load_from_db(npc_monster_details['monster'])
            current_monster.name = npc_monster_details['name']
            current_monster.level = npc_monster_details['level']
            current_monster.hp = npc_monster_details['hp']
            current_monster.current_hp = npc_monster_details['hp']
            current_monster.attack = npc_monster_details['attack']
            current_monster.defense = npc_monster_details['defense']
            current_monster.speed = npc_monster_details['speed']
            current_monster.special_attack = npc_monster_details['special_attack']
            current_monster.special_defense = npc_monster_details['special_defense']
            current_monster.experience_give_modifier = npc_monster_details['exp_give_mod']
            current_monster.experience_required_modifier = npc_monster_details['exp_req_mod']

            current_monster.type1 = results['types'][0]

            current_monster.set_level(current_monster.level)

            if len(results['types']) > 1:
                current_monster.type2 = results['types'][1]

            current_monster.load_sprite_from_db()

            pound = technique.Technique('technique_pound')

            current_monster.learn(pound)

            # Add our monster to the NPC's party
            npc.monsters.append(current_monster)

        # Add our players and setup combat
        logger.debug("Starting battle!")
        self.game.push_state("CombatState", players=(self.game.player1, npc), combat_type="trainer")

        # Start some music!
        logger.info("Playing battle music!")
        filename = "147066_pokemon.ogg"

        mixer.music.load(prepare.BASEDIR + "resources/music/" + filename)
        mixer.music.play(-1)

        if self.game.current_music["song"]:
            self.game.current_music["previoussong"] = self.game.current_music["song"]
        self.game.current_music["status"] = "playing"
        self.game.current_music["song"] = filename

    def update(self):
        if self.game.get_state_name("CombatState") is None:
            self.stop()
