# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, final

from tuxemon import save
from tuxemon.constants.asset_loader import fetch_asset
from tuxemon.event.eventaction import EventAction
from tuxemon.player import Player
from tuxemon.prepare import PLAYER_NPC
from tuxemon.session import Session
from tuxemon.states.world_state import WorldState

logger = logging.getLogger(__name__)


@final
@dataclass
class LoadGameAction(EventAction):
    """
    Loads the game.

    If the index parameter is absent, then it'll load
    slot4.save

    index = 0 > slot 1
    index = 1 > slot 2
    index = 2 > slot 3

    Script usage:
        .. code-block::

            load_game [index]

    Script parameters:
        index: Selected index.

    eg: "load_game" (slot4.save)
    eg: "load_game 1"
    """

    name = "load_game"
    index: Optional[int] = None

    def start(self, session: Session) -> None:
        client = session.client
        index = 4 if self.index is None else self.index + 1

        client.map_loader.clear_cache()
        logger.info("Loading!")

        save_path = save.get_save_path(index)
        save_data = save.load(save_path)
        if not save_data:
            return

        try:
            old_world = client.get_state_by_name(WorldState)
            client.remove_state_by_name("LoadMenuState")
            client.pop_state(old_world)
            client.remove_state_by_name("WorldMenuState")
        except ValueError:
            client.remove_state_by_name("LoadMenuState")
            if self.index is not None:
                client.remove_state_by_name("StartState")

        npc_state = save_data.npc_state
        if npc_state is None:
            logger.error("Save data missing NPC state.")
            return

        slug = npc_state.player_slug or PLAYER_NPC
        npc_state.player_slug = slug
        Player.create(session, slug=slug)

        if npc_state.current_map is None:
            logger.error("Save data missing current map.")
            return

        map_path = fetch_asset("maps", npc_state.current_map)
        client.push_state("WorldState", session=session, map_name=map_path)

        session.load_state(save_data)

        if npc_state.tile_pos is None:
            logger.error("Save data missing tile position.")
            return

        tele_x, tele_y = npc_state.tile_pos
        params = ["player", npc_state.current_map, tele_x, tele_y]
        client.current_music.stop()
        client.event_engine.execute_action("teleport", params)
