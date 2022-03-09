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

from __future__ import annotations
from tuxemon import monster

import json, random, tuxemon, logging
import tuxemon.npc
from tuxemon import ai
from tuxemon.db import db

from tuxemon.combat import check_battle_legal
from tuxemon.event.eventaction import EventAction
from typing import Union, NamedTuple, final, Optional
from os import listdir
from tuxemon.states.world.worldstate import WorldState
from tuxemon.states.combat.combat import CombatState
class AddMonsterActionParameters(NamedTuple):

    monster_level: int
    npc_slug: str
    tile_pos_x: int
    tile_pos_y: int
    animations: Union[str, None]
    behavior: Union[str, None]


logger = logging.getLogger(__name__)
@final
class randomfight(EventAction[AddMonsterActionParameters]):
    """
    a

    """

    name = "random_fight"
    param_class = AddMonsterActionParameters


    def start(self) -> None:
        file_path = 'tuxemon/db/monster/'
        mon_files = listdir(file_path)
        mon_slug_list = []
        player = self.session.player
        jsondata = []
        for i in range(len(mon_files)):
            f = str(mon_files[i])
            mon_path = str(file_path + f)
            curfile = open(mon_path)
            data = json.load(curfile)
            jsondata.append(data)
            slug = data['slug']
            mon_slug_list.append(slug)
        for j in range(6):
            monster_slug = random.choice(mon_slug_list)
            current_monster = monster.Monster()
            current_monster.load_from_db(monster_slug)
            current_monster.set_level(5)
            current_monster.current_hp = current_monster.hp

            player.add_monster(current_monster)
        
        # Get a copy of the world state.
        world = self.session.client.get_state_by_name(WorldState)

        # Get the npc's parameters from the action
        slug = '37707_male'

        # Ensure that the NPC doesn't already exist on the map.
        if slug in world.npcs:
            return

        # Get the npc's parameters from the action
        pos_x = 0
        pos_y = 0
        behavior = 'wander'

        sprite = False
        if sprite:
            logger.warning(
                "%s: setting npc sprites within a map is deprecated, and may be removed in the future. "
                "Sprites should be defined in JSON before loading.",
                slug,
            )
        else:
            sprite = db.database["npc"][slug].get("sprite_name")

        # Create a new NPC object
        npc = tuxemon.npc.NPC(slug, sprite_name=sprite, world=world)
        npc.set_position((pos_x, pos_y))

        # Set the NPC object's variables
        npc.behavior = behavior
        npc.ai = ai.RandomAI()
        npc.load_party()

        for k in range(6):
            monster_slug = random.choice(mon_slug_list)
            current_monster = monster.Monster()
            current_monster.load_from_db(monster_slug)
            current_monster.set_level(5)
            current_monster.current_hp = current_monster.hp
            npc.add_monster(current_monster)
        
        # Don't start a battle if we don't even have monsters in our party yet.
        if not check_battle_legal(player):
            logger.debug("battle is not legal, won't start")
            return

        world = self.session.client.get_state_by_name(WorldState)


        # Lookup the environment
        env_slug = "grass"
        if "environment" in player.game_variables:
            env_slug = player.game_variables["environment"]
        env = db.lookup(env_slug, table="environment")

        # Add our players and setup combat
        logger.debug("Starting battle!")
        self.session.client.push_state(
            CombatState,
            players=(player, npc),
            combat_type="player",
            graphics=env["battle_graphics"],
        )

        # Start some music!
        filename = env["battle_music"]
        self.session.client.event_engine.execute_action(
            "play_music",
            [filename],
        )

    def update(self) -> None:
        try:
            self.session.client.get_state_by_name(CombatState)
        except ValueError:
            self.stop()
