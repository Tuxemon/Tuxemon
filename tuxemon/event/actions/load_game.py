# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, final

from tuxemon import prepare, save
from tuxemon.event.eventaction import EventAction
from tuxemon.states.world.worldstate import WorldState

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

    def start(self) -> None:
        client = self.session.client
        index = 4 if self.index is None else self.index + 1

        logger.info("Loading!")
        save_data = save.load(index)
        if save_data and "error" not in save_data["npc_state"]:
            try:
                old_world = client.get_state_by_name(WorldState)
                # when game is loaded from world menu
                client.pop_state()
                client.pop_state(old_world)
                client.pop_state()
            except ValueError:
                # when game is loaded from the start menu
                client.pop_state()
                # avoid crash save and load same action
                if self.index is not None:
                    client.pop_state()

            map_path = prepare.fetch(
                "maps", save_data["npc_state"]["current_map"]
            )
            client.push_state(
                WorldState(
                    map_name=map_path,
                )
            )

            # TODO: Get player from whatever place and use self.client in
            # order to build a Session
            self.session.player.set_state(self.session, save_data["npc_state"])

            # teleport the player to the correct position using an event
            # engine action
            tele_x, tele_y = save_data["npc_state"]["tile_pos"]
            params = [
                "player",
                save_data["npc_state"]["current_map"],
                tele_x,
                tele_y,
            ]
            client.event_engine.execute_action("teleport", params)
