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
import logging
import random

from tuxemon import ai, monster, prepare
from tuxemon.combat import check_battle_legal
from tuxemon.db import db, JSONEncounterItem
from tuxemon.event.eventaction import EventAction
from tuxemon.npc import NPC
from typing import NamedTuple, Union, final, Sequence, Optional
from tuxemon.states.world.worldstate import WorldState
from tuxemon.states.combat.combat import CombatState
from tuxemon.states.transition.flash import FlashTransition

logger = logging.getLogger(__name__)


class RandomEncounterActionParameters(NamedTuple):
    encounter_slug: str
    total_prob: Union[float, None]


@final
class RandomEncounterAction(EventAction[RandomEncounterActionParameters]):
    """
    Randomly start a encounter.

    Randomly starts a battle with a monster defined in the "encounter" table
    in the "monster.db" database. The chance that this will start a battle
    depends on the "encounter_rate" specified in the database. The
    "encounter_rate" number is the chance
    walking in to this tile will trigger a battle out of 100.
    "total_prob" is an optional override which scales the probabilities so
    that the sum is equal to "total_prob".

    Script usage:
        .. code-block::

            random_encounter <encounter_slug>[,total_prob]

    Script parameters:
        encounter_slug: Slug of the encounter list.
        total_prob: Total sum of the probabilities.

    """

    name = "random_encounter"
    param_class = RandomEncounterActionParameters

    def start(self) -> None:
        player = self.session.player
        self.world = None

        # Don't start a battle if we don't even have monsters in our party yet.
        if not check_battle_legal(player):
            return

        slug = self.parameters.encounter_slug
        encounters = db.lookup(slug, table="encounter")["monsters"]
        encounter = _choose_encounter(encounters, self.parameters.total_prob)

        # If a random encounter was successfully rolled, look up the monster
        # and start the battle.
        if encounter:
            logger.info("Starting random encounter!")

            self.world = self.session.client.get_state_by_name(WorldState)
            npc = _create_monster_npc(encounter, world=self.world)

            # Lookup the environment
            env_slug = "grass"
            if "environment" in player.game_variables:
                env_slug = player.game_variables["environment"]
            env = db.lookup(env_slug, table="environment")

            # Add our players and setup combat
            # "queueing" it will mean it starts after the top of the stack
            # is popped (or replaced)
            self.session.client.queue_state(
                "CombatState",
                players=(player, npc),
                combat_type="monster",
                graphics=env["battle_graphics"],
            )

            # stop the player
            self.world.lock_controls()
            self.world.stop_player()

            # flash the screen
            self.session.client.push_state(FlashTransition)

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

    def cleanup(self) -> None:
        npc = None
        if self.world:
            self.world.remove_entity("random_encounter_dummy")

def _choose_encounter(
    encounters: Sequence[JSONEncounterItem],
    total_prob: Optional[float],
) -> Optional[JSONEncounterItem]:
    total = 0.0
    roll = random.random() * 100
    if total_prob is not None:
        current_total = sum(
            encounter["encounter_rate"] for encounter in encounters
        )
        scale = float(total_prob) / current_total
    else:
        scale = 1

    scale *= prepare.CONFIG.encounter_rate_modifier

    for encounter in encounters:
        total += encounter["encounter_rate"] * scale
        if total >= roll:
            return encounter

    return None


def _create_monster_npc(
    encounter: JSONEncounterItem,
    world: WorldState,
) -> NPC:
    current_monster = monster.Monster()
    current_monster.load_from_db(encounter["monster"])
    # Set the monster's level based on the specified level range
    if len(encounter["level_range"]) > 1:
        level = random.randrange(
            encounter["level_range"][0],
            encounter["level_range"][1],
        )
    else:
        level = encounter["level_range"][0]
    # Set the monster's level
    current_monster.level = 1
    current_monster.set_level(level)
    current_monster.current_hp = current_monster.hp

    # Create an NPC object which will be this monster's "trainer"
    npc = NPC("random_encounter_dummy", world=world)
    npc.add_monster(current_monster)
    # NOTE: random battles are implemented as trainer battles.
    #       this is a hack. remove this once trainer/random battlers are fixed
    current_monster.owner = None
    npc.party_limit = 0

    # Set the NPC object's AI model.
    npc.ai = ai.RandomAI()
    return npc
