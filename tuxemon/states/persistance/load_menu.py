# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from typing import Optional

from tuxemon import prepare, save
from tuxemon.menu.interface import MenuItem
from tuxemon.session import local_session
from tuxemon.states.world.worldstate import WorldState

from .save_menu import SaveMenuState

logger = logging.getLogger(__name__)


class LoadMenuState(SaveMenuState):
    def __init__(self, load_slot: Optional[int] = None) -> None:
        super().__init__()
        if load_slot:
            self.selected_index = load_slot - 1
            self.on_menu_selection(None)

    def on_menu_selection(self, menuitem: Optional[MenuItem[None]]) -> None:
        save_data = save.load(self.selected_index + 1)
        if save_data and "error" not in save_data:

            try:
                old_world = self.client.get_state_by_name(WorldState)
                # when game is loaded from world menu
                self.client.pop_state(self)
                self.client.pop_state(old_world)
            except ValueError:
                # when game is loaded from the start menu
                self.client.pop_state()
                self.client.pop_state()

            map_path = prepare.fetch("maps", save_data["current_map"])
            self.client.push_state(
                WorldState(
                    map_name=map_path,
                )
            )

            # TODO: Get player from whatever place and use self.client in
            # order to build a Session
            local_session.player.set_state(local_session, save_data)

            # teleport the player to the correct position using an event
            # engine action
            tele_x, tele_y = save_data["tile_pos"]
            params = [save_data["current_map"], tele_x, tele_y]
            self.client.event_engine.execute_action("teleport", params)
