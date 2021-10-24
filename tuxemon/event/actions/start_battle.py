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

from tuxemon.combat import check_battle_legal
from tuxemon.db import db
from tuxemon.event.eventaction import EventAction
from typing import NamedTuple, final
from tuxemon.states.world.worldstate import WorldState
from tuxemon.states.combat.combat import CombatState

logger = logging.getLogger(__name__)


class StartBattleActionParameters(NamedTuple):
    npc_slug: str


@final
class StartBattleAction(EventAction[StartBattleActionParameters]):
    """
    Start a battle with the given npc and switch to the combat module.

    Script usage:
        .. code-block::

            start_battle <npc_slug>

    Script parameters:
        npc_slug: Either "player" or npc slug name (e.g. "npc_maple").

    """

    name = "start_battle"
    param_class = StartBattleActionParameters

    def start(self) -> None:
        player = self.session.player

        # Don't start a battle if we don't even have monsters in our party yet.
        if not check_battle_legal(player):
            logger.debug("battle is not legal, won't start")
            return

        world = self.session.client.get_state_by_name(WorldState)

        npc = world.get_entity(self.parameters.npc_slug)
        assert npc
        if len(npc.monsters) == 0:
            return

        # Lookup the environment
        env_slug = "grass"
        if "environment" in player.game_variables:
            env_slug = player.game_variables["environment"]
        env = db.lookup(env_slug, table="environment")

        # Add our players and setup combat
        logger.debug("Starting battle!")
        self.session.client.push_state(
            "CombatState",
            players=(player, npc),
            combat_type="trainer",
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
